import requests
import time

URL = "http://127.0.0.1:8001/agent"

tests = [
    "Write a Python script that calculates the factorial of 7, save it as factorial.py, and run it.",
    "Write a Python script with a syntax error on purpose, run it, see the error, then fix it and run it again successfully.",
    "List all files currently in the workspace.",
    "Search for how to reverse a string in Python, then write a script demonstrating it.",
    "Deploy this code to AWS Lambda."
]

for i, test in enumerate(tests, 1):
    print(f"\n{'='*40}")
    print(f"RUNNING TEST {i}: {test}")
    print(f"{'='*40}")
    
    start_time = time.time()
    try:
        response = requests.post(URL, json={"task": test}, timeout=120)
        response.raise_for_status()
        data = response.json()
        print(f"\nFinal Answer: {data.get('final_answer')}")
        print(f"Total Steps: {data.get('total_steps')}")
    except Exception as e:
        print(f"\nTest {i} failed with error: {e}")
    
    print(f"Time taken: {time.time() - start_time:.2f} seconds")
    time.sleep(2)
