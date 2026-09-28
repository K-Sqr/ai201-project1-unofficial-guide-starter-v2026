"""
Stages 3 and 4 of the pipeline: embedding chunks and retrieving them.

Three things in here are worth knowing about, because they'd quietly break the
rest of the project if they were wrong:

1. The Chroma collection is created with cosine distance, explicitly. Chroma
   defaults to squared L2, and the 0.6 threshold the course uses is calibrated
   against cosine. Getting this wrong makes every distance number meaningless.

2. `search` returns the distance alongside each chunk. Milestone 4 has you
   compare distances, so they have to be visible.

3. The embedding model is the one Chroma bundles, not one loaded through
   `sentence-transformers`. It is the same model — `all-MiniLM-L6-v2`, 384
   dimensions — but it arrives as an ONNX build from Chroma's own CDN, so the
   install needs neither PyTorch nor a reachable Hugging Face. See `_embedder`.
"""

import os
import re
import shutil
from dataclasses import dataclass

# Must be set BEFORE chromadb is imported. Without it, some Chroma versions
# print "Failed to send telemetry event ..." on every single call — which looks
# exactly like a real error, isn't one, and cost a previous cohort a lot of
# confused help-channel messages.
os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")

import chromadb  # noqa: E402

import config
from chunker import Chunk


@dataclass
class Result:
    """One retrieved chunk and how far it was from the question."""

    text: str
    source: str
    label: str
    distance: float   # LOWER IS BETTER. 0.3 is close, 0.9 is unrelated.
    produced_by: str


_model = None

# The model Chroma bundles. Anything else in config.EMBEDDING_MODEL means
# "fetch that one from Hugging Face instead" — see `_embedder`.
BUNDLED_MODEL = "all-MiniLM-L6-v2"


class _OnnxEmbedder:
    """
    Chroma's built-in embedder, wrapped to look like the other two.

    Chroma's embedding functions are called directly and hand back numpy
    arrays. The rest of this file wants `.encode(texts)`, so the adapter lives
    here rather than making every caller care which embedder it got.
    """

    def __init__(self):
        from chromadb.utils.embedding_functions import ONNXMiniLM_L6_V2

        self._ef = ONNXMiniLM_L6_V2()

    def encode(self, texts, show_progress_bar: bool = False):
        return [vector.tolist() for vector in self._ef(list(texts))]


def _sentence_transformer(name: str):
    """
    The escape hatch: any model that isn't the bundled one.

    Unit 2's "try a second embedding model" stretch option comes through here,
    and so does anything you set `EMBEDDING_MODEL` to. This path *does* need
    `sentence-transformers` and a reachable Hugging Face, neither of which the
    default install has — which is the whole point of the default install.
    """
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:
        raise RuntimeError(
            f"config.EMBEDDING_MODEL is set to {name!r}, which isn't the model "
            f"Chroma bundles ({BUNDLED_MODEL!r}), so it has to be downloaded "
            f"from Hugging Face.\n"
            f"Install the optional dependency first:\n"
            f"    pip install 'sentence-transformers>=3.4,<3.5'\n"
            f"Or set EMBEDDING_MODEL back to {BUNDLED_MODEL!r}."
        ) from exc

    return SentenceTransformer(name)


def _embedder():
    """
    Load the embedding model once and keep it.

    First call is slow — it downloads about 80 MB. That's why setup happens
    before class.
    """
    global _model

    if _model is not None:
        return _model

    # Used only by this repo's own smoke test, which runs where no model can be
    # downloaded at all. Never set this yourself.
    if os.getenv("AI201_FAKE_EMBEDDINGS") == "1":
        from _smoke_embedder import FakeEmbedder

        _model = FakeEmbedder()
    elif config.EMBEDDING_MODEL == BUNDLED_MODEL:
        _model = _OnnxEmbedder()
    else:
        _model = _sentence_transformer(config.EMBEDDING_MODEL)

    return _model


def embed(texts: list[str]) -> list[list[float]]:
    """Turn text into vectors. Runs on your machine, costs no API quota."""
    vectors = _embedder().encode(texts, show_progress_bar=False)
    # sentence-transformers and the smoke stand-in return something with a
    # .tolist(); _OnnxEmbedder has already done that conversion itself.
    return vectors.tolist() if hasattr(vectors, "tolist") else vectors


def _client():
    return chromadb.PersistentClient(
        path=str(config.CHROMA_DIR),
        settings=chromadb.config.Settings(anonymized_telemetry=False),
    )


def build_index(
    chunks: list[Chunk],
    corpus: str | None = None,
    variant: str = "default",
) -> int:
    """
    Embed every chunk and store it.

    `variant` lets you keep more than one index of the same corpus at the same
    time. In unit 2, when you compare two chunking strategies, index the second
    one as variant="v2" and you can query both instead of deleting the first
    and starting over.
    """
    name = config.collection_name(corpus, variant)
    client = _client()

    try:
        client.delete_collection(name)
    except Exception:
        pass

    collection = client.create_collection(
        name=name,
        # ⚠️ Do not remove. Chroma defaults to squared L2, and every distance
        # number in this course assumes cosine.
        metadata={"hnsw:space": "cosine"},
    )

    batch = 256
    for start in range(0, len(chunks), batch):
        window = chunks[start : start + batch]
        collection.add(
            ids=[f"{c.source}#{c.index}" for c in window],
            documents=[c.text for c in window],
            embeddings=embed([c.text for c in window]),
            metadatas=[
                {"source": c.source, "index": c.index, "produced_by": c.produced_by}
                for c in window
            ],
        )

    return len(chunks)


def _embedding_search(
    question: str,
    top_k: int,
    collection,
) -> list[Result]:
    """
    The starter's original retrieval: nearest neighbours by embedding distance
    alone. Kept so unit 2's hybrid search has something to compare against —
    same shape as `chunker.py::fallback_split` next to `split_documents`.
    """
    raw = collection.query(
        query_embeddings=embed([question]),
        n_results=min(top_k, collection.count()),
    )

    results: list[Result] = []
    for text, meta, distance in zip(
        raw["documents"][0], raw["metadatas"][0], raw["distances"][0]
    ):
        results.append(
            Result(
                text=text,
                source=str(meta.get("source", "unknown")),
                label=f"{meta.get('source', 'unknown')}#{meta.get('index', 0)}",
                distance=float(distance),
                produced_by=str(meta.get("produced_by", "unknown")),
            )
        )
    return results


# ─── Hybrid search (unit 2 improvement) ──────────────────────────────────────
#
# Pure embedding search conflates chunks whose wording is generic and
# near-identical — campus_life's seven housing_*_laundry.txt posts, for
# example, differ mostly in a building name and two dollar figures. A question
# that names a building gives BM25 an exact keyword match on that name; plain
# embeddings only have the surrounding sentence, which several buildings
# share almost word for word. Combining the two catches what either one alone
# misses.
#
# BM25OKapi is rebuilt from the whole collection on first use per corpus/
# variant and cached — cheap at this corpus's size (183 chunks) and avoids a
# second on-disk index.

_bm25_cache: dict[str, tuple] = {}

BM25_WEIGHT = 0.5   # how much lexical overlap counts against embedding similarity
POOL_MULTIPLIER = 4  # how much wider than top_k the re-ranked candidate pool is


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def _bm25_for(name: str, collection):
    """BM25 index over every chunk in this collection, id-aligned."""
    if name in _bm25_cache:
        return _bm25_cache[name]

    from rank_bm25 import BM25Okapi

    data = collection.get(include=["documents", "metadatas"])
    ids = data["ids"]
    docs = data["documents"]
    bm25 = BM25Okapi([_tokenize(d) for d in docs])

    cached = (bm25, ids)
    _bm25_cache[name] = cached
    return cached


def _hybrid_search(
    question: str,
    top_k: int,
    name: str,
    collection,
) -> list[Result]:
    """
    Re-rank a wider embedding candidate pool by blending embedding similarity
    with BM25 lexical overlap, then keep the top_k.

    Distances on the returned Results are still real embedding distances —
    gate.py's cutoff was calibrated against those, and re-ranking which chunk
    comes first doesn't change what "close" means.
    """
    pool_size = min(collection.count(), max(top_k * POOL_MULTIPLIER, 20))
    pool = _embedding_search(question, pool_size, collection)
    if not pool:
        return pool

    bm25, ids = _bm25_for(name, collection)
    scores = bm25.get_scores(_tokenize(question))
    scores_by_id = dict(zip(ids, scores))
    max_bm25 = max(scores) if len(scores) else 0.0

    def combined_score(result: Result) -> float:
        sim_embed = 1.0 - result.distance
        bm25_raw = scores_by_id.get(result.label, 0.0)
        bm25_norm = (bm25_raw / max_bm25) if max_bm25 > 0 else 0.0
        return (1 - BM25_WEIGHT) * sim_embed + BM25_WEIGHT * bm25_norm

    pool.sort(key=combined_score, reverse=True)
    return pool[:top_k]


def search(
    question: str,
    top_k: int | None = None,
    corpus: str | None = None,
    variant: str = "default",
) -> list[Result]:
    """
    Retrieve the chunks closest to a question, hybrid-ranked (unit 2 — see
    `_hybrid_search`): embedding similarity blended with BM25 keyword overlap,
    over a wider embedding candidate pool. Returns them nearest-first, each
    with its (embedding) distance.
    """
    top_k = top_k or config.TOP_K
    name = config.collection_name(corpus, variant)

    try:
        collection = _client().get_collection(name)
    except Exception as exc:
        raise RuntimeError(
            f"No index called '{name}'. Run `python app.py index` first."
        ) from exc

    return _hybrid_search(question, top_k, name, collection)


def index_exists(corpus: str | None = None, variant: str = "default") -> bool:
    """Is there an index here to search, without searching it?

    `serve.py`'s health check asks this. It deliberately does not embed
    anything: loading the embedding model takes 80 MB and a few seconds, and a
    health check that heavy is a health check nobody can afford to call.
    """
    try:
        collection = _client().get_collection(config.collection_name(corpus, variant))
        return collection.count() > 0
    except Exception:
        return False


def reset():
    """Delete every index. Occasionally the fastest way out of a mess."""
    if config.CHROMA_DIR.exists():
        shutil.rmtree(config.CHROMA_DIR)
