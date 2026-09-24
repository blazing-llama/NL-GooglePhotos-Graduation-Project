import csv
import json
import os
import time
from google_play_scraper import reviews, Sort

def fetch_massive_reviews(target_count=10000):
    print(f"Initializing massive scrape for {target_count} reviews...")
    all_reviews = []
    continuation_token = None
    
    # Batch size for google_play_scraper is usually 199. We loop until we hit the target.
    while len(all_reviews) < target_count:
        try:
            result, continuation_token = reviews(
                'com.google.android.apps.photos',
                lang='en',
                country='us',
                sort=Sort.NEWEST,
                count=199,
                continuation_token=continuation_token
            )
            all_reviews.extend(result)
            print(f"Fetched {len(all_reviews)} reviews so far...")
            
            if not continuation_token:
                print("No more reviews available.")
                break
            time.sleep(1) # Be polite to the API
        except Exception as e:
            print(f"Error fetching reviews: {e}")
            break
            
    return all_reviews[:target_count]

def filter_deep_retrieval_reviews(all_reviews):
    """
    Broadened keyword net to catch specific behavioral workarounds and memory states.
    """
    keywords = [
        'search', 'find', 'looking for', 'remember', 'retrieve', 
        'where is', 'lost', 'scroll', 'scrolling', 'date', 'year',
        'years ago', 'can\'t find', 'difficult to find', 'hard to find',
        'ai search', 'ask photos', 'type', 'typed', 'showed me',
        'wrong', 'irrelevant', 'give up', 'gave up', 'tried', 'album',
        'tag', 'face', 'location'
    ]
    
    filtered = []
    for review in all_reviews:
        content = str(review.get('content', '')).lower()
        if any(keyword in content for keyword in keywords):
            filtered.append(review)
            
    return filtered

def main():
    print("--- STEP 1: MASSIVE DATA INGESTION ---")
    raw_reviews = fetch_massive_reviews(target_count=10000)
    print(f"\nFetched {len(raw_reviews)} total reviews.")
    
    print("\n--- STEP 2: BEHAVIORAL FILTERING ---")
    search_reviews = filter_deep_retrieval_reviews(raw_reviews)
    print(f"Filtered down to {len(search_reviews)} highly relevant retrieval experiences.")
    
    output_json = 'massive_retrieval_corpus.json'
    with open(output_json, 'w', encoding='utf-8') as f:
        # default=str handles every datetime field (at, repliedAt, ...),
        # not just 'at' -- google_play_scraper returns several.
        json.dump(search_reviews, f, indent=2, ensure_ascii=False, default=str)
        
    print(f"\nCorpus saved to {output_json}. Ready for LLM structured extraction.")
    print("\nNext step: Run `llm_analyzer.py` (uses local Ollama, no API key needed) to map this corpus to the 10 Opportunity Areas.")

if __name__ == '__main__':
    main()
