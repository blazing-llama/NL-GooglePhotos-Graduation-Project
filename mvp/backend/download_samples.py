import os
import requests
from concurrent.futures import ThreadPoolExecutor

PHOTOS_DIR = "photos"
os.makedirs(PHOTOS_DIR, exist_ok=True)

# We will download 50 images from Picsum. We use seeded IDs to get a mix of landscapes, objects, architecture.
# Picsum ids span from 1 to ~1000.
def download_image(img_id):
    path = os.path.join(PHOTOS_DIR, f"image_{img_id}.jpg")
    if os.path.exists(path):
        return
    url = f"https://picsum.photos/id/{img_id}/400/400"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            with open(path, 'wb') as f:
                f.write(response.content)
            print(f"Downloaded {path}")
    except Exception as e:
        print(f"Failed to download {img_id}: {e}")

if __name__ == "__main__":
    # Pick 50 diverse IDs
    ids = list(range(10, 60))
    print("Downloading 50 sample photos for MVP testing...")
    with ThreadPoolExecutor(max_workers=5) as executor:
        executor.map(download_image, ids)
    print("Done downloading photos.")
