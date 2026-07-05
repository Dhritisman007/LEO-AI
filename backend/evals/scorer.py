def score_result(test_case: dict, agent_result: dict) -> dict:
    """
    Checks whether LEO's output satisfies the test case validation.
    Returns: {passed, reason, score}
    """
    validation = test_case.get("validation", {})
    v_type = validation.get("type")
    final_answer = agent_result.get("final_answer", "") or ""
    steps = agent_result.get("steps", [])

    # Collect all stdout from tool results across steps
    all_stdout = ""
    for step in steps:
        result = step.get("result", {})
        if isinstance(result, dict):
            all_stdout += result.get("stdout", "") + "\n"

    all_stdout = all_stdout.strip()

    # ── Validation types ─────────────────────────────────────────

    if v_type == "stdout_contains":
        expected = validation["expected"]
        passed = expected in all_stdout
        return {
            "passed": passed,
            "score": 1.0 if passed else 0.0,
            "reason": f"stdout {'contained' if passed else 'did not contain'} '{expected}'",
            "stdout_seen": all_stdout[:300]
        }

    if v_type == "stdout_contains_all":
        expected_list = validation["expected"]
        results = {e: e in all_stdout for e in expected_list}
        passed = all(results.values())
        missing = [e for e, found in results.items() if not found]
        return {
            "passed": passed,
            "score": sum(results.values()) / len(results),
            "reason": f"stdout missing: {missing}" if missing else "all expected strings found in stdout",
            "stdout_seen": all_stdout[:300]
        }

    if v_type == "final_answer_contains":
        expected = validation["expected"]
        passed = expected.lower() in final_answer.lower()
        return {
            "passed": passed,
            "score": 1.0 if passed else 0.0,
            "reason": f"final answer {'contained' if passed else 'did not contain'} '{expected}'",
            "final_answer_seen": final_answer[:300]
        }

    return {"passed": False, "score": 0.0, "reason": "Unknown validation type"}
