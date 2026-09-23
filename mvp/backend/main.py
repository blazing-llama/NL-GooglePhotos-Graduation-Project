from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from database import MOCK_PHOTOS, CATEGORICAL_KEYS, get_facet_values
from parser import parse_vague_query

app = FastAPI(title="Ask Photos Co-Pilot")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

# A result set at or below this size is considered narrow enough to stop refining.
DONE_THRESHOLD = 4


def _matches(photo, filters):
    for key, value in filters.items():
        if not value:
            continue
        field = photo.get(key)
        if isinstance(field, list):
            if value not in field:
                return False
        elif str(field).lower() != str(value).lower():
            return False
    return True


def _filter_photos(filters):
    return [photo for photo in MOCK_PHOTOS if _matches(photo, filters)]


def _suggest_facets(filtered, filters):
    """
    For every facet the user hasn't pinned yet, look only at what's actually
    present in the currently-filtered pool. Only surface a facet as a
    clarifying question if it would meaningfully split that pool (more
    than one distinct value present) -- this is the hallucination guardrail:
    we only ever ask about attributes we can prove exist in the data.
    """
    suggestions = {}
    for key in CATEGORICAL_KEYS:
        if filters.get(key):
            continue
        options = get_facet_values(key, filtered)
        if len(options) > 1:
            suggestions[key] = options[:4]
    return suggestions


def _public_photo(photo):
    return {
        "id": photo["id"],
        "url": photo["url"],
        "location": photo["location"],
        "setting": photo["setting"],
        "weather": photo["weather"],
        "people": photo["people"],
        "object": photo["object"],
    }


def _respond(filters):
    filtered = _filter_photos(filters)
    suggestions = _suggest_facets(filtered, filters)
    done = len(filtered) <= DONE_THRESHOLD or not suggestions
    return {
        "filters": filters,
        "results": [_public_photo(p) for p in filtered],
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
    First turn: parse a vague natural-language query into structured facets
    (zero-hallucination -- every non-null value is guaranteed to exist in the
    catalog), filter the catalog, and return either results or clarifying
    facet suggestions.
    """
    data = await request.json()
    query = data.get("query", "")
    parsed_filters = parse_vague_query(query)
    return _respond(parsed_filters)


@app.post("/api/refine")
async def refine(request: Request):
    """
    Follow-up turn: the user tapped a suggestion chip (or cleared one).
    No LLM call here at all -- purely deterministic filtering over the
    already-established facet state.
    """
    data = await request.json()
    filters = data.get("filters", {})
    filters = {key: filters.get(key) for key in CATEGORICAL_KEYS}
    return _respond(filters)


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
