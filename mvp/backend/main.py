from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

import statistics

from database import ALL_PHOTOS
import image_index

app = FastAPI(title="Ask Photos Co-Pilot")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/photos", StaticFiles(directory="photos"), name="photos")
app.mount("/static", StaticFiles(directory="static"), name="static")

PHOTOS_BY_ID = {p["id"]: p for p in ALL_PHOTOS}

# Semantic search casts a fairly wide net; a result set at or below this
# size is considered narrow enough to stop asking clarifying questions.
SEMANTIC_TOP_K = 40
DONE_THRESHOLD = 8
DISPLAY_LIMIT = 24

# Clarifying chips are generated only from the top slice of the ranked pool
# (the photos that are *actually* strong matches), not the whole 40-wide
# semantic pool -- otherwise chips barely change between queries, since a
# small catalog means most of it survives into any top-40.
SUGGESTION_POOL_SIZE = 10

# A photo whose normalized+boosted score falls below this is considered "not
# actually about what was asked" and dropped, rather than padding out
# results (and clarifying chips) with barely-related photos just because the
# catalog is small. Keeping RELEVANCE_FLOOR_MIN_RESULTS guarantees the user
# still sees *something* even for a query that matches nothing well.
RELEVANCE_FLOOR = -0.2
RELEVANCE_FLOOR_MIN_RESULTS = 6

# An exact keyword/tag hit is worth more than embedding-similarity noise --
# this is what makes "Goa" reliably surface Goa-tagged photos on top.
KEYWORD_MATCH_BOOST = 2.0


@app.on_event("startup")
async def startup_event():
    image_index.build_index()


def _matches_filters(photo, filters):
    facets = photo.get("facets", {})
    for key, value in filters.items():
        if not value:
            continue
        field = facets.get(key)
        if isinstance(field, list):
            if value not in field:
                return False
        elif str(field).lower() != str(value).lower():
            return False
    return True


def _flatten_facet_values(facets):
    values = []
    for val in facets.values():
        if isinstance(val, list):
            values.extend(v for v in val if v)
        elif val:
            values.append(val)
    return values


def _keyword_boost(query, photo):
    """
    +KEYWORD_MATCH_BOOST for every facet/tag value (e.g. "Goa", "rainy",
    "hot chocolate") that literally appears in the query. This is a
    deterministic, explainable signal layered on top of the fuzzier
    embedding score -- so typing an exact place or object name is
    guaranteed to matter, not just nudge the ranking.
    """
    query_lower = query.lower()
    boost = 0.0
    for value in _flatten_facet_values(photo.get("facets", {})):
        if str(value).lower() in query_lower:
            boost += KEYWORD_MATCH_BOOST
    return boost


def _ranked_photos(query):
    """
    Ranks the whole catalog against the query. Three layers:

    1. Raw CLIP cosine similarity (semantic closeness).
    2. Per-source z-score normalization, correcting for CLIP's text-vs-image
       "modality gap" (text queries sit structurally closer to other text
       embeddings than to real image embeddings, so raw cosine similarity
       would always rank mock/text-description photos above real dataset
       photos regardless of actual relevance).
    3. A keyword/tag exact-match boost, so a literal place or object name in
       the query reliably outranks embedding noise.

    Anything that still scores below RELEVANCE_FLOOR is dropped rather than
    padded into the results just because the catalog is small -- that's what
    was making every search show the same handful of location chips
    regardless of relevance.
    """
    scores = image_index.raw_scores(query)

    by_source = {}
    for photo in ALL_PHOTOS:
        by_source.setdefault(photo["source"], []).append(scores[photo["id"]])

    stats = {}
    for source, values in by_source.items():
        mean = statistics.fmean(values)
        stdev = statistics.pstdev(values) or 1.0
        stats[source] = (mean, stdev)

    combined = {}
    for photo in ALL_PHOTOS:
        mean, stdev = stats[photo["source"]]
        z = (scores[photo["id"]] - mean) / stdev
        combined[photo["id"]] = z + _keyword_boost(query, photo)

    ranked_ids = sorted(combined, key=combined.get, reverse=True)

    above_floor = [pid for pid in ranked_ids if combined[pid] >= RELEVANCE_FLOOR]
    if len(above_floor) < RELEVANCE_FLOOR_MIN_RESULTS:
        above_floor = ranked_ids[:RELEVANCE_FLOOR_MIN_RESULTS]

    kept = above_floor[:SEMANTIC_TOP_K]
    return [PHOTOS_BY_ID[pid] for pid in kept], {pid: scores[pid] for pid in kept}


def _suggest_facets(pool, filters):
    """
    Only ask about a facet if it's both unpinned and actually varies within
    the current pool -- guarantees every clarifying chip corresponds to a
    real, provable split in the data (no hallucinated questions).
    """
    suggestions = {}
    keys = set()
    for photo in pool:
        keys.update(photo.get("facets", {}).keys())

    for key in sorted(keys):
        if filters.get(key):
            continue
        values = set()
        for photo in pool:
            val = photo.get("facets", {}).get(key)
            if isinstance(val, list):
                values.update(val)
            elif val:
                values.add(val)
        if len(values) > 1:
            suggestions[key] = sorted(values)[:4]
    return suggestions


def _public_photo(photo, score=None):
    out = {
        "id": photo["id"],
        "url": photo["url"],
        "source": photo["source"],
        "facets": photo.get("facets", {}),
    }
    if score is not None:
        out["score"] = round(score, 3)
    return out


def _respond(pool, filters, scores=None):
    filtered = [p for p in pool if _matches_filters(p, filters)]
    suggestions = _suggest_facets(filtered[:SUGGESTION_POOL_SIZE], filters)
    done = len(filtered) <= DONE_THRESHOLD or not suggestions
    results = filtered[:DISPLAY_LIMIT]
    return {
        "filters": filters,
        "results": [
            _public_photo(p, scores.get(p["id"]) if scores else None) for p in results
        ],
        "count": len(filtered),
        "suggestions": suggestions,
        "done": done,
    }


@app.get("/", response_class=HTMLResponse)
async def serve_ui():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return f.read()


@app.post("/api/ask")
async def ask(request: Request):
    """
    First turn: real CLIP semantic search over the whole catalog (both real
    dataset images and mock photos, ranked in one shared embedding space),
    narrowed further by clarifying facet chips where the pool still varies.
    """
    data = await request.json()
    query = data.get("query", "")
    pool, scores = _ranked_photos(query)
    return _respond(pool, {}, scores)


@app.post("/api/refine")
async def refine(request: Request):
    """
    Follow-up turn: the user tapped a suggestion chip. Re-runs the same
    semantic search for the original query (cheap -- corpus is small) and
    applies the accumulated facet filters on top. No extra model call for
    the filtering step itself.
    """
    data = await request.json()
    query = data.get("query", "")
    filters = data.get("filters", {})

    pool, scores = _ranked_photos(query)
    return _respond(pool, filters, scores)


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
