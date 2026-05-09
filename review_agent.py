import json
import os
import subprocess
import time
from pathlib import Path

import chromadb
from openai import OpenAI
from sentence_transformers import SentenceTransformer


client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

rag_client = chromadb.PersistentClient(path="./chroma_db")
collection = rag_client.get_or_create_collection("policies")
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")


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


def run_tests() -> str:
    result = subprocess.run(
        ["python3", "-m", "pytest"],
        capture_output=True,
        text=True,
    )
    return result.stdout + "\n" + result.stderr


def generate_retrieval_query(diff: str) -> str:
    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "Generate a concise semantic search query for retrieving "
                    "relevant engineering, security, privacy, and code review policies."
                ),
            },
            {
                "role": "user",
                "content": f"PR diff:\n{diff}\n\nReturn only the search query.",
            },
        ],
    )

    return response.choices[0].message.content.strip()


def retrieve_relevant_policies(query: str, n_results: int = 3):
    query_embedding = embedding_model.encode(query).tolist()

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
    )

    return results["documents"][0]


def keyword_search(query: str):
    policy_paths = [
        "policies/pii_policy.md",
        "policies/security_policy.md",
        "policies/code_review_policy.md",
    ]

    matches = []
    query_terms = query.lower().split()

    for path in policy_paths:
        content = Path(path).read_text()
        score = sum(1 for term in query_terms if term in content.lower())

        if score > 0:
            matches.append((score, content))

    matches.sort(reverse=True, key=lambda x: x[0])
    return [doc for _, doc in matches]


def rerank_documents(query: str, documents):
    important_terms = {
        "pii": 5,
        "email": 5,
        "privacy": 4,
        "security": 3,
        "customer": 3,
        "payment": 3,
        "auth": 3,
        "logging": 3,
        "logs": 3,
        "tests": 2,
        "maintainability": 1,
    }

    generic_terms = {
        "policy",
        "policies",
        "guidelines",
        "engineering",
        "review",
        "code",
        "related",
        "compliance",
    }

    scored = []
    query_terms = set(query.lower().replace(",", "").split())

    for doc in documents:
        doc_lower = doc.lower()
        score = 0

        for term in query_terms:
            if term in generic_terms:
                continue

            if term in doc_lower:
                score += important_terms.get(term, 1)

        scored.append((score, doc))

    scored.sort(reverse=True, key=lambda x: x[0])

    print("\n=== RERANKED DOCUMENTS ===\n")
    for i, (score, doc) in enumerate(scored, 1):
        print(f"--- Rank {i} | Score {score} ---")
        print(doc[:250])
        print()

    return [doc for _, doc in scored]


def hybrid_retrieve(query: str, n_results: int = 3):
    semantic_results = retrieve_relevant_policies(query, n_results=n_results)
    keyword_results = keyword_search(query)

    combined = []
    seen = set()

    for doc in semantic_results + keyword_results:
        if doc not in seen:
            combined.append(doc)
            seen.add(doc)

    reranked = rerank_documents(query, combined)
    return reranked[:n_results]


def main():
    start_time = time.time()
    model = "gpt-4.1-mini"

    diff = get_git_diff()
    test_output = run_tests()

    retrieval_query = generate_retrieval_query(diff)
    print(f"\n=== RETRIEVAL QUERY ===\n{retrieval_query}")

    retrieved_policies = hybrid_retrieve(retrieval_query, n_results=3)
    retrieved_context = "\n\n".join(retrieved_policies)

    print("\n=== RETRIEVED POLICIES ===\n")
    print(retrieved_context)

    prompt = f"""
You are reviewing a pull request for a retail checkout service.

Use:
- the PR diff
- test output
- retrieved company policies

Important rules:
- Distinguish between issues introduced by the PR and issues fixed by the PR.
- Do not treat removed code as an active new issue.
- Only flag issues with concrete evidence.
- Do not hallucinate policy violations.
- If tests fail, explain the failure and why it matters.
- Prioritize security, privacy, PII exposure, maintainability, and test coverage.

=== RETRIEVED POLICY CONTEXT ===
{retrieved_context}

=== TEST OUTPUT ===
{test_output}

=== PR DIFF ===
{diff}

Return output in exactly this structure:

## Summary

## Findings

For each finding include:
- Severity
- Evidence
- Violated Policy
- Explanation

## Recommendations

## Overall Assessment
"""

    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": """
You are an enterprise AI code reviewer.

Your goal is to produce a concise, useful PR review comment.
Be specific, evidence-based, and practical.
Do not over-flag low-confidence issues.
""",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
    )

    review = response.choices[0].message.content
    latency_seconds = round(time.time() - start_time, 2)

    print("\n=== AI REVIEW OUTPUT ===\n")
    print(review)

    review_lower = review.lower()

    fix_detected = any(
        phrase in review_lower
        for phrase in [
            "fixed",
            "removes",
            "removed",
            "fix",
            "fixes",
            "mitigates",
            "remediates",
            "eliminates",
            "eliminating",
            "no longer logs",
        ]
    )

    active_issue_detected = any(
        phrase in review_lower
        for phrase in [
            "violates",
            "violation",
            "pii exposure",
            "privacy risk",
            "active issue",
            "introduced",
            "test fails",
            "failing test",
        ]
    )

    eval_passed = fix_detected and not (
        "introduces a pii issue" in review_lower
        or "introduces pii exposure" in review_lower
        or "new pii issue" in review_lower
        or "new privacy risk" in review_lower
    )

    print("\n=== SIMPLE EVAL RESULT ===\n")

    if eval_passed:
        print("PASS: AI reviewer recognized this PR fixes/remediates the PII issue.")
    else:
        print("CHECK: Review may contain an active issue or the eval needs refinement.")

    log_event = {
        "model": model,
        "latency_seconds": latency_seconds,
        "eval_name": "structured_ai_pr_review",
        "eval_passed": eval_passed,
        "active_issue_detected": active_issue_detected,
        "fix_detected": fix_detected,
        "retrieval_query": retrieval_query,
        "retrieved_policy_count": len(retrieved_policies),
        "tokens_used": response.usage.total_tokens if response.usage else None,
    }

    Path("logs").mkdir(exist_ok=True)

    with open("logs/review_log.jsonl", "a") as f:
        f.write(json.dumps(log_event) + "\n")


if __name__ == "__main__":
    main()
