import json
import requests
import time

# Use local Ollama instance (100% Free, No Token Limits)
OLLAMA_API_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3" # You can change this to 'mistral' or whatever you have pulled in Ollama

SYSTEM_PROMPT = """
You are an expert Product Manager and Behavioral Researcher. 
Your task is to analyze user reviews and extract specific retrieval failures based on the 7-Stage Retrieval Journey and 10 Opportunity Areas.

Extract a JSON object with this EXACT schema for the core problem identified in the review:
{
  "Opportunity": "What users are trying to accomplish",
  "User_segment": "Who experiences it",
  "Memory_state": "What users remember",
  "Behavior": "How they attempt retrieval",
  "Failure_point": "Where the journey breaks",
  "Evidence": "Exact quote",
  "Pattern": "Common mechanism",
  "Workaround": "What users do instead",
  "Impact": "Emotional consequences",
  "Opportunity_size": "High/Medium/Low",
  "Open_question": "What needs validation"
}
Ensure output is ONLY valid JSON.
"""

def analyze_with_ollama(review_text):
    prompt = f"{SYSTEM_PROMPT}\n\nReview to analyze:\n{review_text}"
    
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,
        "format": "json" # Forces Ollama to output valid JSON
    }
    
    try:
        response = requests.post(OLLAMA_API_URL, json=payload)
        response.raise_for_status()
        result = response.json()
        return json.loads(result.get("response", "{}"))
    except Exception as e:
        print(f"Ollama API error: {e}")
        return None

def process_corpus(reviews_file):
    print(f"Connecting to local Ollama ({MODEL_NAME}) for FREE processing...")
    
    try:
        with open(reviews_file, 'r', encoding='utf-8') as f:
            reviews = json.load(f)
    except FileNotFoundError:
        print(f"Could not find {reviews_file}. Run the scraper first.")
        return

    print(f"Loaded {len(reviews)} reviews. Starting local LLM extraction...\n")
    
    extracted_problems = []
    
    # Process the first 10 for testing so it doesn't take hours immediately. 
    # Change to `reviews` to process all 10,000.
    for i, review in enumerate(reviews[:10]):
        content = review.get('content', '')
        if len(content) < 20: 
            continue # Skip very short reviews
            
        print(f"Processing Review {i+1}...")
        extracted_json = analyze_with_ollama(content)
        
        if extracted_json:
            extracted_problems.append(extracted_json)
            
    # Save the structured problem map
    with open('ollama_problem_map.json', 'w', encoding='utf-8') as f:
        json.dump(extracted_problems, f, indent=2)
        
    print(f"\nSuccessfully processed and saved {len(extracted_problems)} problem maps to ollama_problem_map.json")

if __name__ == "__main__":
    process_corpus('massive_retrieval_corpus.json')
