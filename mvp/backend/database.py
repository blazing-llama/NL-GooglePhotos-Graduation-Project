"""
Mock photo catalog for the Ask Photos Co-Pilot MVP.

Each entry is a deliberately rich, multi-layered semantic record —
this is the "ground truth" the deterministic filter engine matches
against. Image URLs are seeded picsum.photos placeholders so the UI
has something real to render without a real photo library.
"""

MOCK_PHOTOS = [
    {
        "id": "photo_001",
        "url": "https://picsum.photos/seed/goa-shack-rain/500/500",
        "description": "Sitting at a wooden table at a beach shack cafe in Goa, raining outside.",
        "location": "Goa",
        "setting": "Outdoor",
        "weather": "Rainy",
        "people": ["Friends"],
        "object": "Wooden table",
        "year": "2022",
    },
    {
        "id": "photo_002",
        "url": "https://picsum.photos/seed/manali-hike/500/500",
        "description": "Hiking in the mountains during a cloudy afternoon in Manali with family.",
        "location": "Manali",
        "setting": "Mountain",
        "weather": "Cloudy",
        "people": ["Family"],
        "object": "Backpack",
        "year": "2023",
    },
    {
        "id": "photo_003",
        "url": "https://picsum.photos/seed/mumbai-pasta/500/500",
        "description": "Dinner at a cozy indoor Italian cafe in Mumbai, ordering pasta with friends.",
        "location": "Mumbai",
        "setting": "Indoor",
        "weather": "Clear",
        "people": ["Friends"],
        "object": "Pasta plate",
        "year": "2024",
    },
    {
        "id": "photo_004",
        "url": "https://picsum.photos/seed/bali-beach-rain/500/500",
        "description": "Walking on a rainy beach in Bali with my dog at sunset.",
        "location": "Bali",
        "setting": "Outdoor",
        "weather": "Rainy",
        "people": ["Alone"],
        "object": "Dog",
        "year": "2024",
    },
    {
        "id": "photo_005",
        "url": "https://picsum.photos/seed/kerala-shack/500/500",
        "description": "Rainy evening at a beach shack in Kerala with college friends.",
        "location": "Kerala",
        "setting": "Outdoor",
        "weather": "Rainy",
        "people": ["Friends"],
        "object": "Wooden table",
        "year": "2025",
    },
    {
        "id": "photo_006",
        "url": "https://picsum.photos/seed/manali-snow/500/500",
        "description": "Snowy mountain peak near Manali, sunny and clear sky, alone.",
        "location": "Manali",
        "setting": "Mountain",
        "weather": "Sunny",
        "people": ["Alone"],
        "object": "Snow",
        "year": "2021",
    },
    {
        "id": "photo_007",
        "url": "https://picsum.photos/seed/mumbai-wifi/500/500",
        "description": "Screenshot of a wifi password note taken at a Mumbai cafe.",
        "location": "Mumbai",
        "setting": "Indoor",
        "weather": "Clear",
        "people": [],
        "object": "Screenshot",
        "year": "2024",
    },
    {
        "id": "photo_008",
        "url": "https://picsum.photos/seed/goa-sunny-beach/500/500",
        "description": "Sunny beach afternoon in Goa with family, building sandcastles.",
        "location": "Goa",
        "setting": "Outdoor",
        "weather": "Sunny",
        "people": ["Family"],
        "object": "Sandcastle",
        "year": "2023",
    },
    {
        "id": "photo_009",
        "url": "https://picsum.photos/seed/bali-hotel/500/500",
        "description": "Poolside at a hotel in Bali, cloudy morning, with friends.",
        "location": "Bali",
        "setting": "Indoor",
        "weather": "Cloudy",
        "people": ["Friends"],
        "object": "Pool",
        "year": "2024",
    },
    {
        "id": "photo_010",
        "url": "https://picsum.photos/seed/kerala-backwaters/500/500",
        "description": "Houseboat on the Kerala backwaters, sunny day, with family.",
        "location": "Kerala",
        "setting": "Outdoor",
        "weather": "Sunny",
        "people": ["Family"],
        "object": "Houseboat",
        "year": "2025",
    },
    {
        "id": "photo_011",
        "url": "https://picsum.photos/seed/manali-cafe/500/500",
        "description": "Warm cafe in Manali, rainy outside, hot chocolate with friends.",
        "location": "Manali",
        "setting": "Indoor",
        "weather": "Rainy",
        "people": ["Friends"],
        "object": "Hot chocolate",
        "year": "2022",
    },
    {
        "id": "photo_012",
        "url": "https://picsum.photos/seed/goa-dog-sunset/500/500",
        "description": "Sunset walk on Goa beach with my dog, clear skies, alone.",
        "location": "Goa",
        "setting": "Outdoor",
        "weather": "Clear",
        "people": ["Alone"],
        "object": "Dog",
        "year": "2025",
    },
]

CATEGORICAL_KEYS = ["location", "setting", "weather", "people", "object"]


def get_facet_values(key, photos=None):
    """Unique values present for a facet key across a set of photos (defaults to full catalog)."""
    pool = photos if photos is not None else MOCK_PHOTOS
    values = set()
    for photo in pool:
        val = photo.get(key)
        if isinstance(val, list):
            values.update(val)
        elif val:
            values.add(val)
    return sorted(v for v in values if v)
