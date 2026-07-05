"""
Each test case has:
- id: unique name
- task: what you send to LEO as a prompt
- validation_code: Python code that validates LEO's output
  (has access to `workspace_dir` and `stdout` from LEO's run)
- category: what capability it tests
- max_steps: how many agent steps to allow
"""

TEST_CASES = [

    # ── TIER 1: Basic code generation ──────────────────────────────

    {
        "id": "basic_hello_world",
        "category": "basic",
        "task": "Write a Python script called hello.py that prints exactly: Hello from LEO. Then run it.",
        "max_steps": 6,
        "validation": {
            "type": "stdout_contains",
            "expected": "Hello from LEO"
        }
    },

    {
        "id": "basic_math",
        "category": "basic",
        "task": "Write a Python script called math_test.py that calculates 17 * 23 and prints only the result. Run it.",
        "max_steps": 6,
        "validation": {
            "type": "stdout_contains",
            "expected": "391"
        }
    },

    {
        "id": "basic_list_ops",
        "category": "basic",
        "task": "Write a Python script that sorts the list [5, 2, 8, 1, 9, 3] and prints the sorted result. Save as sort_test.py and run it.",
        "max_steps": 6,
        "validation": {
            "type": "stdout_contains",
            "expected": "[1, 2, 3, 5, 8, 9]"
        }
    },

    # ── TIER 2: Functions and logic ─────────────────────────────────

    {
        "id": "fibonacci",
        "category": "functions",
        "task": "Write a Python function that returns the nth Fibonacci number. Test it with n=10 (answer should be 55). Save as fib.py and run it.",
        "max_steps": 8,
        "validation": {
            "type": "stdout_contains",
            "expected": "55"
        }
    },

    {
        "id": "is_prime",
        "category": "functions",
        "task": "Write a Python function that checks if a number is prime. Test it with 17 (should print True) and 15 (should print False). Save as prime.py and run it.",
        "max_steps": 8,
        "validation": {
            "type": "stdout_contains_all",
            "expected": ["True", "False"]
        }
    },

    {
        "id": "palindrome",
        "category": "functions",
        "task": "Write a Python function that checks if a string is a palindrome. Test with 'racecar' (True) and 'hello' (False). Save as palindrome.py and run it.",
        "max_steps": 8,
        "validation": {
            "type": "stdout_contains_all",
            "expected": ["True", "False"]
        }
    },

    # ── TIER 3: File operations ─────────────────────────────────────

    {
        "id": "file_write_read",
        "category": "file_ops",
        "task": "Write the text 'LEO was here' to a file called note.txt, then read it back and print its contents.",
        "max_steps": 8,
        "validation": {
            "type": "final_answer_contains",
            "expected": "LEO was here"
        }
    },

    {
        "id": "multi_file",
        "category": "file_ops",
        "task": "Create two Python files: utils.py with a function called add(a, b) that returns a+b, and main.py that imports utils and prints add(10, 20). Run main.py.",
        "max_steps": 10,
        "validation": {
            "type": "stdout_contains",
            "expected": "30"
        }
    },

    # ── TIER 4: Error handling ──────────────────────────────────────

    {
        "id": "self_correction",
        "category": "error_handling",
        "task": "Write a Python script with a deliberate syntax error (a missing colon after an if statement). Run it, observe the error, fix it, and run it again successfully. The fixed script should print 'Fixed!'",
        "max_steps": 12,
        "validation": {
            "type": "stdout_contains",
            "expected": "Fixed!"
        }
    },

    {
        "id": "missing_capability",
        "category": "error_handling",
        "task": "Send an email to test@example.com saying hello from LEO.",
        "max_steps": 6,
        "validation": {
            "type": "final_answer_contains",
            "expected": "ERROR"
        }
    },

    # ── TIER 5: Multi-step reasoning ───────────────────────────────

    {
        "id": "search_then_code",
        "category": "reasoning",
        "task": "Search for how Python's enumerate() function works, then write a script that uses enumerate to print the index and value of each item in ['apple', 'banana', 'cherry']. Save as enum_demo.py and run it.",
        "max_steps": 12,
        "validation": {
            "type": "stdout_contains_all",
            "expected": ["apple", "banana", "cherry"]
        }
    },

    {
        "id": "data_processing",
        "category": "reasoning",
        "task": "Write a Python script that takes this list of numbers [4, 7, 2, 9, 1, 5, 8, 3, 6] and prints: the sum, the average, the max, and the min. Save as stats.py and run it.",
        "max_steps": 10,
        "validation": {
            "type": "stdout_contains_all",
            "expected": ["45", "5.0", "9", "1"]
        }
    },
]
