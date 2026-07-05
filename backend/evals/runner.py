import time
import json
import os
from evals.test_cases import TEST_CASES
from evals.scorer import score_result
from agent import run_agent

RESULTS_DIR = "/tmp/leo_eval_results"
os.makedirs(RESULTS_DIR, exist_ok=True)


def run_single_eval(test_case: dict, user_id: str = "eval_user") -> dict:
    """Run one test case through LEO and score it."""
    print(f"\n{'─'*50}")
    print(f"Running: [{test_case['id']}] — {test_case['category']}")
    print(f"Task: {test_case['task'][:80]}...")

    start = time.time()

    try:
        agent_result = run_agent(
            task=test_case["task"],
            max_steps=test_case.get("max_steps", 10),
            user_id=user_id
        )
    except Exception as e:
        agent_result = {
            "final_answer": f"ERROR: agent crashed — {str(e)}",
            "steps": [],
            "plan": []
        }

    elapsed = time.time() - start
    score = score_result(test_case, agent_result)

    result = {
        "id": test_case["id"],
        "category": test_case["category"],
        "task": test_case["task"],
        "passed": score["passed"],
        "score": score["score"],
        "reason": score["reason"],
        "steps_taken": len(agent_result.get("steps", [])),
        "max_steps": test_case.get("max_steps", 10),
        "elapsed_seconds": round(elapsed, 1),
        "final_answer": agent_result.get("final_answer", "")[:300],
    }

    status = "✅ PASS" if result["passed"] else "❌ FAIL"
    print(f"{status} | score: {result['score']:.1f} | steps: {result['steps_taken']}/{result['max_steps']} | time: {result['elapsed_seconds']}s")
    print(f"Reason: {result['reason']}")

    return result


def run_all_evals(
    categories: list = None,
    user_id: str = "eval_user"
) -> dict:
    """
    Run all (or filtered) test cases and produce a summary report.
    categories: optional list like ["basic", "functions"] to run only those
    """
    cases = TEST_CASES
    if categories:
        cases = [c for c in cases if c["category"] in categories]

    print(f"\n{'='*50}")
    print(f"LEO EVAL RUN — {len(cases)} test cases")
    if categories:
        print(f"Categories: {categories}")
    print(f"{'='*50}")

    results = []
    for case in cases:
        result = run_single_eval(case, user_id=user_id)
        results.append(result)
        time.sleep(1)  # small pause between tests to avoid rate limiting Gemini

    # Build summary
    total = len(results)
    passed = sum(1 for r in results if r["passed"])
    avg_score = sum(r["score"] for r in results) / total if total else 0
    avg_steps = sum(r["steps_taken"] for r in results) / total if total else 0
    avg_time = sum(r["elapsed_seconds"] for r in results) / total if total else 0

    by_category = {}
    for r in results:
        cat = r["category"]
        if cat not in by_category:
            by_category[cat] = {"total": 0, "passed": 0}
        by_category[cat]["total"] += 1
        if r["passed"]:
            by_category[cat]["passed"] += 1

    summary = {
        "total_cases": total,
        "passed": passed,
        "failed": total - passed,
        "pass_rate": round(passed / total * 100, 1) if total else 0,
        "avg_score": round(avg_score, 2),
        "avg_steps": round(avg_steps, 1),
        "avg_time_seconds": round(avg_time, 1),
        "by_category": by_category,
        "results": results
    }

    # Save results to file
    timestamp = int(time.time())
    results_file = os.path.join(RESULTS_DIR, f"eval_{timestamp}.json")
    with open(results_file, "w") as f:
        json.dump(summary, f, indent=2)

    print(f"\n{'='*50}")
    print(f"EVAL COMPLETE")
    print(f"Pass rate: {summary['pass_rate']}% ({passed}/{total})")
    print(f"Avg score: {summary['avg_score']}")
    print(f"Avg steps: {summary['avg_steps']}")
    print(f"Avg time:  {summary['avg_time_seconds']}s per task")
    print(f"\nBy category:")
    for cat, stats in by_category.items():
        rate = stats['passed'] / stats['total'] * 100
        print(f"  {cat}: {stats['passed']}/{stats['total']} ({rate:.0f}%)")
    print(f"\nResults saved to: {results_file}")
    print(f"{'='*50}\n")

    return summary
