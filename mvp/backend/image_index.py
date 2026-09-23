"""
CLIP-based semantic search + zero-shot auto-tagging index.

Two jobs:
1. Embed every photo (real pixels for dataset photos, description text for
   mock photos -- both land in the same CLIP space) so free-text queries can
   be ranked by real semantic similarity, not just facet keyword hits.
2. Auto-tag every photo against a fixed vocabulary of ~50 everyday photo
   concepts (places, settings, weather, people, objects, activities) using
   CLIP zero-shot classification. This is what makes tagging *content-
   grounded* instead of "whatever the dataset's folder name happened to be":
   a dataset photo showing a rainy street gets tagged "rainy" and "street"
   because the image itself is closest to those concepts in CLIP space, not
   because a human labeled it that way. Mock photos get tagged the same way
   from their description, so both sources share one vocabulary -- which is
   what lets a query like "Goa" reliably surface Goa-tagged photos instead
   of being drowned out by whatever else happens to rank nearby.

Both embeddings and tags are cached to disk so a restart doesn't re-run the
model (the slow part) unless the catalog actually changed.
"""

import os
import json
import numpy as np

from database import ALL_PHOTOS

EMBED_CACHE_PATH = "embeddings_cache.npz"
TAGS_CACHE_PATH = "tags_cache.json"
MODEL_ID = "openai/clip-vit-base-patch32"

# A fixed, shared vocabulary every photo (real or mock) is auto-tagged
# against. Keeping this vocabulary broad and generic -- rather than tied to
# any one dataset's label set -- is what lets mock "personal memory" photos
# and real dataset photos compete on equal footing.
TAG_VOCAB = [
    # places / destinations
    "Goa", "Manali", "Kerala", "Mumbai", "Bali", "a city street", "a shopping mall",
    "a market", "a beach", "a mountain", "a temple", "a park", "an airport",
    # settings
    "indoors", "outdoors", "a hotel room", "a home interior", "a restaurant",
    "a cafe", "nighttime", "daytime", "an empty space", "a crowded place",
    # weather
    "rainy weather", "sunny weather", "cloudy weather", "snowy weather",
    # people
    "a group of friends", "a family", "one person alone", "a couple", "a portrait of a person",
    # objects / subjects
    "food", "a drink", "coffee", "a dog", "a pet", "a dessert", "a product for sale",
    "a screenshot of text", "a building", "architecture", "a sunset", "a swimming pool",
    "a boat", "snow", "a backpack", "a table", "flowers", "a vehicle", "water",
    # activities
    "hiking", "shopping", "dining", "sightseeing", "walking",
]

TOP_TAGS_PER_PHOTO = 6
TAG_RELEVANCE_MARGIN = 0.03  # a tag must beat the vocab's mean similarity by at least this much

_model = None
_processor = None
_device = "cpu"

_photo_ids = []
_embeddings = None  # (N, D) float32, L2-normalized
_tag_vocab_embeddings = None  # (V, D) float32, L2-normalized
_tags_by_id = {}


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


def _embed_texts(texts):
    import torch
    model, processor = _get_model()
    inputs = processor(text=texts, return_tensors="pt", padding=True, truncation=True).to(_device)
    with torch.no_grad():
        features = model.get_text_features(**inputs).pooler_output
        features = features / features.norm(p=2, dim=-1, keepdim=True)
    return features.cpu().numpy()


def _embed_text(text):
    return _embed_texts([text])[0]


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


def _assign_tags(photo_vec):
    """
    Ranks this one photo's embedding against every vocab tag and keeps the
    ones that clearly stand out *for this photo* (top-K, and only if they
    beat this photo's own mean similarity by a margin). Ranking per-photo
    rather than with a single global threshold sidesteps the text-vs-image
    modality gap entirely -- we never compare across photos here.
    """
    sims = _tag_vocab_embeddings @ photo_vec
    mean = float(sims.mean())
    order = np.argsort(sims)[::-1]
    tags = []
    for i in order[:TOP_TAGS_PER_PHOTO]:
        if sims[i] - mean >= TAG_RELEVANCE_MARGIN:
            tags.append(TAG_VOCAB[i])
    return tags


def build_index(force=False):
    """Embeds + auto-tags every photo in the catalog once, using disk caches."""
    global _photo_ids, _embeddings, _tag_vocab_embeddings, _tags_by_id

    cached_embeds = {}
    if not force and os.path.exists(EMBED_CACHE_PATH):
        data = np.load(EMBED_CACHE_PATH, allow_pickle=True)
        cached_embeds = {pid: vec for pid, vec in zip(data["ids"], data["vecs"])}

    cached_tags = {}
    if not force and os.path.exists(TAGS_CACHE_PATH):
        with open(TAGS_CACHE_PATH, "r", encoding="utf-8") as f:
            cached_tags = json.load(f)

    _tag_vocab_embeddings = _embed_texts(TAG_VOCAB)

    vectors = []
    ids = []
    tags_by_id = {}
    dirty_embeds = False
    dirty_tags = False

    for photo in ALL_PHOTOS:
        pid = photo["id"]

        if pid in cached_embeds:
            vec = cached_embeds[pid]
        else:
            dirty_embeds = True
            if photo["source"] == "dataset":
                vec = _embed_image(photo["local_path"])
            else:
                vec = _embed_text(photo["description"])
            print(f"Embedded {pid}".encode("ascii", "replace").decode())
        ids.append(pid)
        vectors.append(vec)

        if pid in cached_tags:
            tags_by_id[pid] = cached_tags[pid]
        else:
            dirty_tags = True
            tags_by_id[pid] = _assign_tags(vec)

        # Merge auto-tags into the photo's own facets so the generic
        # suggestion/filter engine in main.py picks them up for free.
        photo["facets"]["tags"] = tags_by_id[pid]

    _photo_ids = ids
    _embeddings = np.array(vectors, dtype=np.float32)
    _tags_by_id = tags_by_id

    if dirty_embeds:
        np.savez(EMBED_CACHE_PATH, ids=np.array(ids, dtype=object), vecs=_embeddings)
    if dirty_tags:
        with open(TAGS_CACHE_PATH, "w", encoding="utf-8") as f:
            json.dump(tags_by_id, f, ensure_ascii=False)

    print(f"Index ready: {len(_photo_ids)} photos embedded and tagged.")


def raw_scores(query):
    """Returns {photo_id: cosine_similarity} for every photo in the catalog."""
    if _embeddings is None:
        build_index()
    query_vec = _embed_text(query)
    scores = _embeddings @ query_vec
    return {pid: float(s) for pid, s in zip(_photo_ids, scores)}


def get_tags(photo_id):
    return _tags_by_id.get(photo_id, [])
