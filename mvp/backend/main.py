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


def _ranked_photos(query):
    """
    Ranks the whole catalog against the query, correcting for CLIP's
    text-vs-image "modality gap" (text queries sit structurally closer to
    other text embeddings than to real image embeddings, so raw cosine
    similarity would always rank mock/text-description photos above real
    dataset photos regardless of actual relevance). Normalizing scores to a
    z-score within each source group makes "how good a match is this,
    relative to how well its own modality usually matches" comparable
    across sources, so real photos can compete fairly with mock ones.
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

    normalized = {}
    for photo in ALL_PHOTOS:
        mean, stdev = stats[photo["source"]]
        normalized[photo["id"]] = (scores[photo["id"]] - mean) / stdev

    ranked_ids = sorted(normalized, key=normalized.get, reverse=True)[:SEMANTIC_TOP_K]
    return [PHOTOS_BY_ID[pid] for pid in ranked_ids], {pid: scores[pid] for pid in ranked_ids}


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
    suggestions = _suggest_facets(filtered, filters)
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
