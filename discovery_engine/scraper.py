import csv
from google_play_scraper import reviews, Sort
import os
import json

def fetch_google_photos_reviews(count=1000):
    print(f"Fetching up to {count} reviews for Google Photos...")
    
    result, continuation_token = reviews(
        'com.google.android.apps.photos',
        lang='en',
        country='us',
        sort=Sort.NEWEST,
        count=count 
    )
    
    return result

def filter_search_reviews(all_reviews):
    keywords = [
        'search', 'find', 'looking for', 'remember', 'retrieve', 
        'where is', 'lost', 'scroll', 'scrolling', 'date', 'year',
        'years ago', 'can\'t find', 'difficult to find', 'hard to find',
        'ai search', 'ask photos'
    ]
    
    filtered = []
    for review in all_reviews:
        content = str(review.get('content', '')).lower()
        if any(keyword in content for keyword in keywords):
            filtered.append(review)
            
    return filtered

def main():
    raw_reviews = fetch_google_photos_reviews(count=3000)
    print(f"Fetched {len(raw_reviews)} total reviews.")
    
    search_reviews = filter_search_reviews(raw_reviews)
    print(f"Filtered down to {len(search_reviews)} reviews specifically mentioning search/retrieval.")
    
    output_json = 'filtered_search_reviews.json'
    with open(output_json, 'w', encoding='utf-8') as f:
        # Use default=str to convert any non-serializable objects (like datetime) to string
        json.dump(search_reviews, f, indent=2, ensure_ascii=False, default=str)
        
    if search_reviews:
        output_csv = 'filtered_search_reviews.csv'
        with open(output_csv, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['score', 'content', 'at', 'thumbsUpCount', 'reviewCreatedVersion'])
            for rev in search_reviews:
                writer.writerow([
                    rev.get('score'),
                    rev.get('content'),
                    rev.get('at'),
                    rev.get('thumbsUpCount'),
                    rev.get('reviewCreatedVersion')
                ])
        print(f"Saved data to {output_json} and {output_csv}")
    else:
        print("No matching reviews found.")

if __name__ == '__main__':
    main()

if __name__ == '__main__':
    main()
