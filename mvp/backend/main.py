from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
import torch
import numpy as np
from PIL import Image
from transformers import CLIPProcessor, CLIPModel
from sklearn.cluster import KMeans
import glob

app = FastAPI(title="Google Photos Visual Pruner")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Paths
PHOTOS_DIR = "photos"
os.makedirs(PHOTOS_DIR, exist_ok=True)
app.mount("/photos", StaticFiles(directory=PHOTOS_DIR), name="photos")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Globals
model_id = "openai/clip-vit-base-patch32"
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Loading CLIP model on {device}...")
model = CLIPModel.from_pretrained(model_id).to(device)
processor = CLIPProcessor.from_pretrained(model_id)

image_paths = []
image_embeddings = []

def embed_images():
    global image_paths, image_embeddings
    image_paths = glob.glob(f"{PHOTOS_DIR}/*.jpg") + glob.glob(f"{PHOTOS_DIR}/*.png")
    if not image_paths:
        print(f"No images found in {PHOTOS_DIR}. Please add some.")
        return

    print(f"Embedding {len(image_paths)} images...")
    embeddings = []
    for path in image_paths:
        try:
            image = Image.open(path).convert("RGB")
            inputs = processor(images=image, return_tensors="pt").to(device)
            with torch.no_grad():
                embed = model.get_image_features(**inputs)
                embed = embed / embed.norm(p=2, dim=-1, keepdim=True)
            embeddings.append(embed.cpu().numpy()[0])
        except Exception as e:
            print(f"Error processing {path}: {e}")
            embeddings.append(np.zeros(512)) # fallback
            
    image_embeddings = np.array(embeddings)
    print("Embedding complete.")

@app.on_event("startup")
async def startup_event():
    embed_images()

@app.get("/", response_class=HTMLResponse)
async def serve_ui():
    with open("static/index.html", "r") as f:
        return f.read()

@app.get("/api/search")
async def search(query: str):
    """Initial text search to narrow down the universe."""
    if len(image_embeddings) == 0:
        return {"error": "No images available"}
        
    inputs = processor(text=[query], return_tensors="pt", padding=True).to(device)
    with torch.no_grad():
        text_features = model.get_text_features(**inputs)
        text_features = text_features / text_features.norm(p=2, dim=-1, keepdim=True)
        
    text_emb = text_features.cpu().numpy()[0]
    
    # Cosine similarity
    similarities = (image_embeddings @ text_emb.T).flatten()
    
    # Get top 50 matches to start pruning
    top_indices = np.argsort(similarities)[::-1][:50]
    
    return {
        "indices": top_indices.tolist(),
        "paths": [os.path.basename(image_paths[i]) for i in top_indices]
    }

@app.post("/api/cluster")
async def cluster(request: Request):
    """
    Takes a list of active image indices.
    Runs K-Means (k=2) to find two visual centroids.
    Returns the two centroid images, and the two resulting lists of indices.
    """
    data = await request.json()
    active_indices = data.get("indices", [])
    
    if len(active_indices) <= 2:
        # Pruning is done, return the final images
        return {
            "done": True,
            "final_paths": [os.path.basename(image_paths[i]) for i in active_indices]
        }
        
    active_embeddings = image_embeddings[active_indices]
    
    # K-Means clustering (k=2)
    kmeans = KMeans(n_clusters=2, random_state=42, n_init=10)
    labels = kmeans.fit_predict(active_embeddings)
    
    # Find the images closest to the centroids
    centroids = kmeans.cluster_centers_
    cluster_0_indices = [active_indices[i] for i in range(len(labels)) if labels[i] == 0]
    cluster_1_indices = [active_indices[i] for i in range(len(labels)) if labels[i] == 1]
    
    # Handle edge case where a cluster is empty
    if not cluster_0_indices or not cluster_1_indices:
        return {
            "done": True,
            "final_paths": [os.path.basename(image_paths[i]) for i in active_indices]
        }
        
    # Find closest to centroid 0
    c0_dists = np.linalg.norm(image_embeddings[cluster_0_indices] - centroids[0], axis=1)
    rep0_idx = cluster_0_indices[np.argmin(c0_dists)]
    
    # Find closest to centroid 1
    c1_dists = np.linalg.norm(image_embeddings[cluster_1_indices] - centroids[1], axis=1)
    rep1_idx = cluster_1_indices[np.argmin(c1_dists)]
    
    return {
        "done": False,
        "option_a": {
            "path": os.path.basename(image_paths[rep0_idx]),
            "cluster_indices": cluster_0_indices
        },
        "option_b": {
            "path": os.path.basename(image_paths[rep1_idx]),
            "cluster_indices": cluster_1_indices
        }
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
