"""
CLIP-based semantic search index.

Real dataset photos are embedded from actual pixels (image encoder).
Mock (placeholder) photos are embedded from their text description (text
encoder) -- CLIP's text and image encoders share one embedding space, so a
text-query embedding can be meaningfully compared against both kinds of
vector with a single cosine similarity. This is what fixes "beach" (or any
other free-text query) matching nothing: previously only exact facet
keyword hits counted, now every photo is ranked by real semantic closeness
to the query.

Embeddings are cached to disk (npy) since encoding is the slow part and the
catalog doesn't change between runs.
"""

import os
import numpy as np

from database import ALL_PHOTOS

CACHE_PATH = "embeddings_cache.npz"
MODEL_ID = "openai/clip-vit-base-patch32"

_model = None
_processor = None
_device = "cpu"

_photo_ids = []
_embeddings = None  # (N, D) float32, L2-normalized


def _get_model():
    global _model, _processor, _device
    if _model is None:
        import torch
        from transformers import CLIPModel, CLIPProcessor
        _device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Loading CLIP model ({MODEL_ID}) on {_device}...")
        _model = CLIPModel.from_pretrained(MODEL_ID).to(_device)
        _processor = CLIPProcessor.from_pretrained(MODEL_ID)
    return _model, _processor


def _embed_text(text):
    import torch
    model, processor = _get_model()
    inputs = processor(text=[text], return_tensors="pt", padding=True, truncation=True).to(_device)
    with torch.no_grad():
        features = model.get_text_features(**inputs).pooler_output
        features = features / features.norm(p=2, dim=-1, keepdim=True)
    return features.cpu().numpy()[0]


def _embed_image(path):
    import torch
    from PIL import Image
    model, processor = _get_model()
    image = Image.open(path).convert("RGB")
    inputs = processor(images=image, return_tensors="pt").to(_device)
    with torch.no_grad():
        features = model.get_image_features(**inputs).pooler_output
        features = features / features.norm(p=2, dim=-1, keepdim=True)
    return features.cpu().numpy()[0]


def build_index(force=False):
    """Embeds every photo in the catalog once, using a disk cache keyed by photo id."""
    global _photo_ids, _embeddings

    cached = {}
    if not force and os.path.exists(CACHE_PATH):
        data = np.load(CACHE_PATH, allow_pickle=True)
        cached = {pid: vec for pid, vec in zip(data["ids"], data["vecs"])}

    vectors = []
    ids = []
    dirty = False
    for photo in ALL_PHOTOS:
        pid = photo["id"]
        if pid in cached:
            vec = cached[pid]
        else:
            dirty = True
            if photo["source"] == "dataset":
                vec = _embed_image(photo["local_path"])
            else:
                vec = _embed_text(photo["description"])
            print(f"Embedded {pid}".encode("ascii", "replace").decode())
        ids.append(pid)
        vectors.append(vec)

    _photo_ids = ids
    _embeddings = np.array(vectors, dtype=np.float32)

    if dirty:
        np.savez(CACHE_PATH, ids=np.array(ids, dtype=object), vecs=_embeddings)

    print(f"Index ready: {len(_photo_ids)} photos embedded.")


def raw_scores(query):
    """Returns {photo_id: cosine_similarity} for every photo in the catalog."""
    if _embeddings is None:
        build_index()
    query_vec = _embed_text(query)
    scores = _embeddings @ query_vec
    return {pid: float(s) for pid, s in zip(_photo_ids, scores)}


def search(query, top_k=40):
    """Returns [(photo_id, score), ...] sorted by descending cosine similarity."""
    scores = raw_scores(query)
    ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
    return ranked[:top_k]
