"""
Unified photo catalog for the Ask Photos Co-Pilot MVP.

Combines two sources into one list of records, each shaped as:
    {"id", "url", "description", "source": "mock"|"dataset", "facets": {...}}

- MOCK entries: hand-written personal-memory photos (seeded placeholder
  images) with rich facets (location/setting/weather/people/object) -- good
  for demoing the deterministic chip-narrowing flow end to end.
- DATASET entries: 100 real photos from the Urban-ImageNet "Sample Dataset"
  (https://huggingface.co/datasets/Yiwei-Ou/Urban-ImageNet), downloaded by
  download_dataset.py into photos/dataset/<category_slug>/. Each is tagged
  with a single "category" facet from its folder name -- real images, real
  pixels, real CLIP embeddings.

`facets` keys are intentionally NOT identical across sources. The search
and suggestion engine in main.py works generically over whatever facet keys
are present in a given result set, so the two sources coexist naturally.
"""

import os
import glob

MOCK_PHOTOS = [
    {
        "id": "photo_001",
        "url": "https://picsum.photos/seed/goa-shack-rain/500/500",
        "description": "Sitting at a wooden table at a beach shack cafe in Goa, raining outside.",
        "source": "mock",
        "facets": {
            "location": "Goa", "setting": "Outdoor", "weather": "Rainy",
            "people": ["Friends"], "object": "Wooden table",
        },
    },
    {
        "id": "photo_002",
        "url": "https://picsum.photos/seed/manali-hike/500/500",
        "description": "Hiking in the mountains during a cloudy afternoon in Manali with family.",
        "source": "mock",
        "facets": {
            "location": "Manali", "setting": "Mountain", "weather": "Cloudy",
            "people": ["Family"], "object": "Backpack",
        },
    },
    {
        "id": "photo_003",
        "url": "https://picsum.photos/seed/mumbai-pasta/500/500",
        "description": "Dinner at a cozy indoor Italian cafe in Mumbai, ordering pasta with friends.",
        "source": "mock",
        "facets": {
            "location": "Mumbai", "setting": "Indoor", "weather": "Clear",
            "people": ["Friends"], "object": "Pasta plate",
        },
    },
    {
        "id": "photo_004",
        "url": "https://picsum.photos/seed/bali-beach-rain/500/500",
        "description": "Walking on a rainy beach in Bali with my dog at sunset.",
        "source": "mock",
        "facets": {
            "location": "Bali", "setting": "Outdoor", "weather": "Rainy",
            "people": ["Alone"], "object": "Dog",
        },
    },
    {
        "id": "photo_005",
        "url": "https://picsum.photos/seed/kerala-shack/500/500",
        "description": "Rainy evening at a beach shack in Kerala with college friends.",
        "source": "mock",
        "facets": {
            "location": "Kerala", "setting": "Outdoor", "weather": "Rainy",
            "people": ["Friends"], "object": "Wooden table",
        },
    },
    {
        "id": "photo_006",
        "url": "https://picsum.photos/seed/manali-snow/500/500",
        "description": "Snowy mountain peak near Manali, sunny and clear sky, alone.",
        "source": "mock",
        "facets": {
            "location": "Manali", "setting": "Mountain", "weather": "Sunny",
            "people": ["Alone"], "object": "Snow",
        },
    },
    {
        "id": "photo_007",
        "url": "https://picsum.photos/seed/mumbai-wifi/500/500",
        "description": "Screenshot of a wifi password note taken at a Mumbai cafe.",
        "source": "mock",
        "facets": {
            "location": "Mumbai", "setting": "Indoor", "weather": "Clear",
            "people": [], "object": "Screenshot",
        },
    },
    {
        "id": "photo_008",
        "url": "https://picsum.photos/seed/goa-sunny-beach/500/500",
        "description": "Sunny beach afternoon in Goa with family, building sandcastles.",
        "source": "mock",
        "facets": {
            "location": "Goa", "setting": "Outdoor", "weather": "Sunny",
            "people": ["Family"], "object": "Sandcastle",
        },
    },
    {
        "id": "photo_009",
        "url": "https://picsum.photos/seed/bali-hotel/500/500",
        "description": "Poolside at a hotel in Bali, cloudy morning, with friends.",
        "source": "mock",
        "facets": {
            "location": "Bali", "setting": "Indoor", "weather": "Cloudy",
            "people": ["Friends"], "object": "Pool",
        },
    },
    {
        "id": "photo_010",
        "url": "https://picsum.photos/seed/kerala-backwaters/500/500",
        "description": "Houseboat on the Kerala backwaters, sunny day, with family.",
        "source": "mock",
        "facets": {
            "location": "Kerala", "setting": "Outdoor", "weather": "Sunny",
            "people": ["Family"], "object": "Houseboat",
        },
    },
    {
        "id": "photo_011",
        "url": "https://picsum.photos/seed/manali-cafe/500/500",
        "description": "Warm cafe in Manali, rainy outside, hot chocolate with friends.",
        "source": "mock",
        "facets": {
            "location": "Manali", "setting": "Indoor", "weather": "Rainy",
            "people": ["Friends"], "object": "Hot chocolate",
        },
    },
    {
        "id": "photo_012",
        "url": "https://picsum.photos/seed/goa-dog-sunset/500/500",
        "description": "Sunset walk on Goa beach with my dog, clear skies, alone.",
        "source": "mock",
        "facets": {
            "location": "Goa", "setting": "Outdoor", "weather": "Clear",
            "people": ["Alone"], "object": "Dog",
        },
    },
]

DATASET_DIR = os.path.join("photos", "dataset")

CATEGORY_LABELS = {
    "exterior_with_people": "Exterior urban space (with people)",
    "exterior_no_people": "Exterior urban space (empty)",
    "food_or_drink": "Food or drink",
    "hotel": "Hotel / lodging",
    "portrait": "Portrait",
    "interior_with_people": "Interior urban space (with people)",
    "interior_no_people": "Interior urban space (empty)",
    "other": "Other",
    "home_interior": "Home interior",
    "retail": "Retail / merchandise",
}


def _load_dataset_photos():
    photos = []
    if not os.path.isdir(DATASET_DIR):
        return photos
    for slug, label in CATEGORY_LABELS.items():
        folder = os.path.join(DATASET_DIR, slug)
        for path in sorted(glob.glob(os.path.join(folder, "*.jpg"))):
            filename = os.path.basename(path)
            photos.append({
                "id": f"dataset_{slug}_{filename}",
                "url": f"/photos/dataset/{slug}/{filename}",
                "local_path": path,
                "description": f"A real photo of {label.lower()}.",
                "source": "dataset",
                "facets": {"category": label},
            })
    return photos


DATASET_PHOTOS = _load_dataset_photos()

ALL_PHOTOS = MOCK_PHOTOS + DATASET_PHOTOS


def get_facet_values(key, photos=None):
    """Unique values for a facet key across a set of photos (defaults to the full catalog)."""
    pool = photos if photos is not None else ALL_PHOTOS
    values = set()
    for photo in pool:
        val = photo.get("facets", {}).get(key)
        if isinstance(val, list):
            values.update(val)
        elif val:
            values.add(val)
    return sorted(v for v in values if v)


def get_all_facet_keys(photos=None):
    pool = photos if photos is not None else ALL_PHOTOS
    keys = set()
    for photo in pool:
        keys.update(photo.get("facets", {}).keys())
    return sorted(keys)
