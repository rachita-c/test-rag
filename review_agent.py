import os
import time
import json
import subprocess
from pathlib import Path
from openai import OpenAI

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])


def read_file(path: str) -> str:
    return Path(path).read_text()


def get_git_diff() -> str:
    result = subprocess.run(
        ["git", "show", "--format=", "--unified=3", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout


def main():
    start_time = time.time()
    model = "gpt-4.1-mini"
    diff = get_git_diff()

    pii_policy = read_file("policies/pii_policy.md")
    agents = read_file("AGENTS.md")
    eval_case = read_file("evals/pii_eval.txt")

    prompt = f"""
You are an enterprise AI code reviewer.

Review the following pull request diff.

Focus on:
- security
- privacy
- PII exposure
- maintainability

=== AGENTS.md ===
{agents}

=== PII POLICY ===
{pii_policy}

=== EVAL EXPECTATIONS ===
{eval_case}

=== PR DIFF ===
{diff}

Return:
1. Summary
2. Findings
3. Severity
4. Recommended fix
"""

    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": "You are a senior enterprise code reviewer."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    review = response.choices[0].message.content
    latency_seconds = round(time.time() - start_time, 2)

    eval_passed = "PII" in review or "privacy" in review.lower()

    log_event = {
        "model": model,
        "latency_seconds": latency_seconds,
        "eval_name": "pii_logging_detection",
        "eval_passed": eval_passed,
        "tokens_used": response.usage.total_tokens if response.usage else None,
    }

    Path("logs").mkdir(exist_ok=True)
    with open("logs/review_log.jsonl", "a") as f:
        f.write(json.dumps(log_event) + "\n")
 
    print("\n=== AI REVIEW OUTPUT ===\n")
    print(review)

    print("\n=== SIMPLE EVAL RESULT ===\n")

    if eval_passed:
        print("PASS: AI reviewer detected privacy/PII issue.")
    else:
        print("FAIL: AI reviewer missed expected PII issue.")


if __name__ == "__main__":
    main()
