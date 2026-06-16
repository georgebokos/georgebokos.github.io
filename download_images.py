#!/usr/bin/env python3
import os
import time
import json
import urllib.request
import urllib.parse

IMAGES_DIR = os.path.join(os.path.dirname(__file__), "images")

# Map filename -> Wikipedia article title to fetch the main image
RECIPES = {
    "pasta_thalassina": "Spaghetti alle vongole",
    "saltsa_kotopoulo": "Gravy",
}

UA = "recipe-image-bot/1.0 (educational project; contact g.bokos1984@gmail.com)"

def request_with_retry(url, timeout=20, max_retries=5):
    headers = {"User-Agent": UA}
    delay = 5
    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read()
        except urllib.error.HTTPError as e:
            if e.code == 429:
                print(f"  Rate limit, waiting {delay}s...")
                time.sleep(delay)
                delay *= 2
            else:
                raise
    raise Exception("Max retries exceeded")

def get_wikipedia_image_url(title):
    encoded = urllib.parse.quote(title)
    api_url = (
        f"https://en.wikipedia.org/w/api.php"
        f"?action=query&prop=pageimages&format=json"
        f"&piprop=original&titles={encoded}"
    )
    data = json.loads(request_with_retry(api_url))
    pages = data["query"]["pages"]
    for page in pages.values():
        img = page.get("original", {}).get("source")
        if img:
            return img
    return None

def download_url(url, out_path):
    data = request_with_retry(url, timeout=30)
    if len(data) < 5000:
        return False
    with open(out_path, "wb") as f:
        f.write(data)
    return len(data)

failed = []
for i, (name, wiki_title) in enumerate(RECIPES.items(), 1):
    out_path = os.path.join(IMAGES_DIR, f"{name}.png")
    if os.path.exists(out_path):
        print(f"[{i}/{len(RECIPES)}] SKIP: {name}.png")
        continue

    print(f"[{i}/{len(RECIPES)}] {name} <- '{wiki_title}'")
    try:
        img_url = get_wikipedia_image_url(wiki_title)
        if not img_url:
            print(f"  No image found on Wikipedia")
            failed.append(name)
        else:
            # Wikipedia images can be SVG; skip those
            if img_url.lower().endswith(".svg"):
                print(f"  Wikipedia image is SVG, skipping: {img_url}")
                failed.append(name)
            else:
                size = download_url(img_url, out_path)
                if size:
                    print(f"  OK ({size//1024}KB): {img_url[:80]}")
                else:
                    print(f"  Too small, skipping")
                    failed.append(name)
    except Exception as e:
        print(f"  ERROR: {e}")
        failed.append(name)
    time.sleep(2)

print(f"\nDone. Failed ({len(failed)}): {failed}")
