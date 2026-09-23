"""
Downloads the Urban-ImageNet "Sample Dataset" (100 labeled images, 10 per
category) from Hugging Face into photos/dataset/<category_slug>/, so the
CLIP image index has real, diverse, real-world photos to search over
(not just seeded placeholder images).

Source: https://huggingface.co/datasets/Yiwei-Ou/Urban-ImageNet
License: cc-by-nc-sa-4.0 (non-commercial) -- fine for this academic MVP.
"""

import os
import re
import requests
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import quote

REPO = "Yiwei-Ou/Urban-ImageNet"
BASE_URL = f"https://huggingface.co/datasets/{REPO}/resolve/main"
ROOT_DIR = "Sample Dataset/01 Images with labels"
OUT_DIR = os.path.join("photos", "dataset")

# category folder name -> (slug used on disk, human-readable label kept in metadata)
CATEGORIES = {
    "Exterior urban spaces with people": "exterior_with_people",
    "Exterior urban spaces without people": "exterior_no_people",
    "Food or drink items": "food_or_drink",
    "Hotel or commercial lodging spaces": "hotel",
    "Human-centered portrait": "portrait",
    "Interior urban spaces with people": "interior_with_people",
    "Interior urban spaces without people": "interior_no_people",
    "Other non-spatial content": "other",
    "Private home interiors": "home_interior",
    "Retail products and merchandise": "retail",
}

# Filenames per category, as listed on the Hub (`find` on the repo).
FILES = {
    "Exterior urban spaces with people": [
        "1197195715_2023年12月15日_5.jpg", "1771105160_2020年02月21日_0.jpg",
        "1880879761_2020年10月14日_1.jpg", "1918679231_2020年01月18日_1.jpg",
        "2487783190_2023年05月02日_2.jpg", "2541383303_2023年12月27日_0.jpg",
        "2686917617_2020年08月07日_2.jpg", "2695951785_2023年04月02日_1.jpg",
        "2739826582_2023年08月28日_7.jpg", "2824323062_2020年10月20日_5.jpg",
    ],
    "Exterior urban spaces without people": [
        "1653301903_2020年05月07日_4.jpg", "1844617504_2020年08月23日_2.jpg",
        "1929079164_2023年05月03日_1.jpg", "2022639353_2023年12月04日_4.jpg",
        "2198451705_2020年09月25日_0.jpg", "2247561057_2023年04月16日_6.jpg",
        "2422677620_2023年04月25日_1.jpg", "2456391730_2023年12月28日_1.jpg",
        "2462487490_2020年08月10日_1.jpg", "2474227881_2023年10月15日_1.jpg",
    ],
    "Food or drink items": [
        "1364538275_2020年06月27日_2.jpg", "1564567591_2020年01月09日_8.jpg",
        "1768728344_2020年01月07日_4.jpg", "1782181914_2020年12月29日_1.jpg",
        "1863100830_2023年05月12日_1.jpg", "1919975634_2023年08月01日_1.jpg",
        "1942300581_2020年06月04日_8.jpg", "1963555874_2024年03月28日_21_47_0.jpg",
        "2050672355_2024年02月16日_20_19_0.jpg", "2145202674_2020年01月05日_5.jpg",
    ],
    "Hotel or commercial lodging spaces": [
        "1671953000_2019年02月14日_2.jpg", "1671953000_2019年03月08日_6.jpg",
        "3096276253_2019年08月27日_3.jpg", "5689935576_2019年08月09日_2.jpg",
        "5689935576_2019年09月08日_6.jpg", "5748120859_2019年02月08日_1.jpg",
        "5767344884_2020年04月30日_1.jpg", "6073543841_2020年02月07日_1.jpg",
        "6073543841_2020年02月07日_3.jpg", "6132848456_2020年01月18日_4.jpg",
    ],
    "Human-centered portrait": [
        "1833101035_2023年04月30日_4.jpg", "1888835301_2023年03月13日_4.jpg",
        "2695854681_2020年09月03日_0.jpg", "2739210032_2020年08月03日_0.jpg",
        "2754239217_2023年09月24日_0.jpg", "5024811496_2023年06月19日_2.jpg",
        "5300386229_2023年10月11日_1.jpg", "5305628092_2023年12月18日_7.jpg",
        "5875835705_2023年04月29日_1.jpg", "6768297937_2023年11月28日_0.jpg",
    ],
    "Interior urban spaces with people": [
        "1230390922_2024年11月20日_16_48_5.jpg", "1341216127_2023年07月01日_6.jpg",
        "1579508107_2023年06月29日_7.jpg", "1993674377_2023年10月28日_6.jpg",
        "2194376502_2023年04月24日_4.jpg", "2287911270_2020年03月18日_2.jpg",
        "3843081848_2024年10月21日_22_13_8.jpg", "5648000404_2020年10月03日_0.jpg",
        "5763295410_2024年04月23日_05_49_3.jpg", "5955437474_2023年08月30日_1.jpg",
    ],
    "Interior urban spaces without people": [
        "1253050934_2020年08月25日_8.jpg", "1583275637_2023年11月02日_0.jpg",
        "1619062404_2020年11月18日_5.jpg", "1678519971_2023年10月03日_2.jpg",
        "1741066425_2020年11月05日_0.jpg", "1819773654_2020年07月10日_8.jpg",
        "1937183945_2020年06月10日_8.jpg", "2311896077_2020年09月22日_2.jpg",
        "5622384134_2023年09月16日_5.jpg", "6281622216_2023年12月24日_0.jpg",
    ],
    "Other non-spatial content": [
        "1699262783_2020年08月25日_0.jpg", "2806931833_2023年11月13日_5.jpg",
        "2993469332_2023年07月29日_4.jpg", "5928533673_2020年10月28日_0.jpg",
        "6023352545_2020年10月27日_8.jpg", "6671656712_2020年04月30日_0.jpg",
        "6771235910_2023年04月15日_0.jpg", "7092513531_2020年07月06日_0.jpg",
        "7140326058_2023年08月06日_5.jpg", "7443163077_2020年07月06日_0.jpg",
    ],
    "Private home interiors": [
        "2892778321_2023年03月09日_1.jpg", "3485896247_2020年12月04日_4.jpg",
        "5716158262_2020年10月16日_7.jpg", "5889459283_2020年06月04日_0.jpg",
        "7211057792_2019年10月16日_8.jpg", "7223723273_2020年11月18日_2.jpg",
        "7226678862_2023年03月09日_2.jpg", "7321179083_2023年04月16日_3.jpg",
        "7339807900_2020年09月05日_2.jpg", "7339807900_2020年09月05日_3.jpg",
    ],
    "Retail products and merchandise": [
        "3513260533_2020年04月23日_8.jpg", "5403151541_2020年10月23日_2.jpg",
        "5490074477_2020年10月08日_1.jpg", "5659232333_2024年08月01日_13_29_6.jpg",
        "5756052337_2023年12月25日_2.jpg", "5794781804_2020年09月20日_4.jpg",
        "6216673317_2024年06月19日_18_07_3.jpg", "6382937467_2024年10月01日_17_02_0.jpg",
        "6466002971_2020年12月31日_2.jpg", "7306616910_2023年05月12日_3.jpg",
    ],
}


def _download_one(category, filename):
    slug = CATEGORIES[category]
    out_dir = os.path.join(OUT_DIR, slug)
    os.makedirs(out_dir, exist_ok=True)

    # Keep a filesystem-safe local name; the original filename (with Chinese
    # characters and spaces) is preserved only in the remote URL.
    safe_name = re.sub(r"[^\w.\-]", "_", filename)
    local_path = os.path.join(out_dir, safe_name)
    if os.path.exists(local_path):
        return

    remote_path = f"{ROOT_DIR}/{category}/{filename}"
    url = BASE_URL + "/" + quote(remote_path)

    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        with open(local_path, "wb") as f:
            f.write(response.content)
        print(f"Downloaded {slug}/{safe_name}".encode("ascii", "replace").decode())
    except Exception as e:
        print(f"Failed {slug}: {e}".encode("ascii", "replace").decode())


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    jobs = [(cat, fname) for cat, files in FILES.items() for fname in files]
    print(f"Downloading {len(jobs)} images from {REPO}...")
    with ThreadPoolExecutor(max_workers=8) as executor:
        list(executor.map(lambda job: _download_one(*job), jobs))
    print("Done.")


if __name__ == "__main__":
    main()
