import json
import os
import requests
import time

# Use local Ollama instance (100% Free, No Token Limits)
OLLAMA_API_URL = "http://localhost:11434/api/generate"
# "llama3" isn't a real pulled tag -- use whatever `ollama list` actually shows.
MODEL_NAME = os.environ.get("OLLAMA_MODEL", "llama3.2:3b")
CHECKPOINT_EVERY = 20

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
        response = requests.post(OLLAMA_API_URL, json=payload, timeout=90)
        response.raise_for_status()
        result = response.json()
        return json.loads(result.get("response", "{}"))
    except Exception as e:
        print(f"Ollama API error: {e}".encode("ascii", "replace").decode(), flush=True)
        return None


def process_corpus(reviews_file, limit=None, output_file="ollama_problem_map.json"):
    print(f"Connecting to local Ollama ({MODEL_NAME}) for FREE processing...", flush=True)

    try:
        with open(reviews_file, 'r', encoding='utf-8') as f:
            reviews = json.load(f)
    except FileNotFoundError:
        print(f"Could not find {reviews_file}. Run the scraper first.")
        return

    if limit:
        reviews = reviews[:limit]

    # Resume support: don't re-pay for reviews a previous (possibly
    # interrupted) run already extracted.
    extracted_problems = []
    already_done = set()
    if os.path.exists(output_file):
        try:
            with open(output_file, 'r', encoding='utf-8') as f:
                extracted_problems = json.load(f)
            already_done = {r.get("_source_review") for r in extracted_problems}
            print(f"Resuming: {len(already_done)} reviews already extracted in {output_file}.", flush=True)
        except (json.JSONDecodeError, FileNotFoundError):
            pass

    todo = [r for r in reviews if r.get('content', '') not in already_done]
    print(f"Loaded {len(reviews)} reviews ({len(todo)} remaining). Starting local LLM extraction...\n", flush=True)

    start = time.time()
    done_count = 0

    for review in todo:
        content = review.get('content', '')
        if len(content) < 20:
            continue  # Skip very short reviews

        extracted_json = analyze_with_ollama(content)
        if extracted_json:
            extracted_json["_source_review"] = content
            extracted_json["_score"] = review.get("score")
            extracted_problems.append(extracted_json)

        done_count += 1
        elapsed = time.time() - start
        rate = done_count / elapsed if elapsed > 0 else 0
        remaining = (len(todo) - done_count) / rate if rate > 0 else 0
        print(f"[{done_count}/{len(todo)}] total_extracted={len(extracted_problems)} "
              f"({rate:.2f}/s, ~{remaining/60:.1f} min left)".encode("ascii", "replace").decode(), flush=True)

        if done_count % CHECKPOINT_EVERY == 0:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(extracted_problems, f, indent=2, ensure_ascii=False)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(extracted_problems, f, indent=2, ensure_ascii=False)

    print(f"\nSuccessfully processed and saved {len(extracted_problems)} problem maps to {output_file}", flush=True)

if __name__ == "__main__":
    limit_env = os.environ.get("ANALYZE_LIMIT")
    process_corpus(
        'massive_retrieval_corpus.json',
        limit=int(limit_env) if limit_env else None,
    )
