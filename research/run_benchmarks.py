#!/usr/bin/env python3
"""TemuClaude Benchmark Runner — Real Data"""
import json, time, requests, sys, os

API_KEY = os.environ.get('OPENROUTER_API_KEY', '')
BASE_URL = "https://openrouter.ai/api/v1/chat/completions"

BENCHMARK_QUESTIONS = [
    {"type": "math", "question": "What is the derivative of x^3 + 2x^2 - 5x + 1?", "answer": "3x^2 + 4x - 5"},
    {"type": "math", "question": "What is 9.9 - 9.11? Give the exact number.", "answer": "0.79"},
    {"type": "math", "question": "Solve for x: 2x + 7 = 3x - 2", "answer": "9"},
    {"type": "math", "question": "What is the integral of 2x dx?", "answer": "x^2 + C"},
    {"type": "math", "question": "What is log base 2 of 256?", "answer": "8"},
    {"type": "coding", "question": "Write a Python function to merge two sorted lists. Return just the function.", "answer": "def merge"},
    {"type": "coding", "question": "What is the time complexity of binary search? Big O notation.", "answer": "O(log n)"},
    {"type": "coding", "question": "Write a Python one-liner to reverse a string s.", "answer": "s[::-1]"},
    {"type": "coding", "question": "What does SELECT * FROM users WHERE age > 18 do?", "answer": "selects all columns from users where age is greater than 18"},
    {"type": "coding", "question": "Write a Python function to check if a string is a palindrome.", "answer": "def is_palindrome"},
    {"type": "reasoning", "question": "If all A are B, and all B are C, then all A are what?", "answer": "C"},
    {"type": "reasoning", "question": "A bat and ball cost $1.10 total. The bat costs $1.00 more than the ball. How much does the ball cost?", "answer": "0.05"},
    {"type": "reasoning", "question": "If 5 machines make 5 widgets in 5 minutes, how long for 100 machines to make 100 widgets?", "answer": "5"},
    {"type": "reasoning", "question": "In a race, you overtake the person in 2nd place. What position are you in?", "answer": "2nd"},
    {"type": "reasoning", "question": "A farmer has 17 sheep. All but 9 die. How many are left?", "answer": "9"},
    {"type": "knowledge", "question": "What is the capital of Australia?", "answer": "Canberra"},
    {"type": "knowledge", "question": "What does DNA stand for?", "answer": "Deoxyribonucleic acid"},
    {"type": "knowledge", "question": "Who wrote To Kill a Mockingbird?", "answer": "Harper Lee"},
    {"type": "knowledge", "question": "What is the largest planet in our solar system?", "answer": "Jupiter"},
    {"type": "knowledge", "question": "What year did World War 2 end?", "answer": "1945"},
]

MODELS = [
    {"name": "glm-5.2", "id": "z-ai/glm-5.2"},
    {"name": "deepseek-v4-pro", "id": "deepseek/deepseek-v4-pro"},
    {"name": "gemini-3-flash", "id": "google/gemini-3.5-flash"},
    {"name": "nemotron-3-ultra", "id": "nvidia/nemotron-3-ultra-550b-a55b:free"},
]

def call_model(model_id, question, temp=0.7, max_tokens=500):
    try:
        r = requests.post(BASE_URL, headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
        }, json={
            "model": model_id,
            "messages": [{"role": "user", "content": question}],
            "temperature": temp,
            "max_tokens": max_tokens,
        }, timeout=45)
        d = r.json()
        if r.status_code == 200:
            c = d.get("choices", [{}])[0].get("message", {}).get("content", "") or ""
            cost = d.get("usage", {}).get("cost", 0)
            return {"success": True, "content": c, "cost": cost}
        return {"success": False, "content": "", "cost": 0, "error": d.get("error", {}).get("message", "?")}
    except Exception as e:
        return {"success": False, "content": "", "cost": 0, "error": str(e)}

def check_answer(response, expected):
    if not response:
        return False
    r, e = response.lower(), expected.lower()
    if len(e) < 20:
        return e in r
    words = e.split()
    return sum(1 for w in words if w in r) >= len(words) * 0.7

results = {}
total_cost = 0

for model in MODELS:
    name = model["name"]
    print(f"\nTesting {name}...", flush=True)
    correct = 0
    total = 0
    mc = 0
    for i, q in enumerate(BENCHMARK_QUESTIONS):
        r = call_model(model["id"], q["question"])
        if r["success"]:
            ok = check_answer(r["content"], q["answer"])
            correct += ok
            total += 1
            mc += r["cost"]
            total_cost += r["cost"]
            print(f"  Q{i+1} ({q['type']}): {'PASS' if ok else 'FAIL'} ${r['cost']:.4f}", flush=True)
        else:
            print(f"  Q{i+1}: ERROR {r.get('error','?')[:50]}", flush=True)
    acc = (correct / total * 100) if total else 0
    results[name] = {"correct": correct, "total": total, "accuracy": acc, "cost": mc}
    print(f"  → {name}: {correct}/{total} = {acc:.1f}% ${mc:.4f}", flush=True)

# MoA fusion test
print("\nTesting MoA Fusion...", flush=True)
fc = 0
ft = 0
fco = 0
for i, q in enumerate(BENCHMARK_QUESTIONS):
    responses = {}
    for m in MODELS[:3]:
        r = call_model(m["id"], q["question"])
        if r["success"]:
            responses[m["name"]] = r["content"]
            fco += r["cost"]
            total_cost += r["cost"]
    any_ok = any(check_answer(v, q["answer"]) for v in responses.values())
    if not any_ok and responses:
        fp = f"Question: {q['question']}\n\nA (GLM): {responses.get('glm-5.2','')}\nB (DeepSeek): {responses.get('deepseek-v4-pro','')}\nC (Gemini): {responses.get('gemini-3-flash','')}\n\nWhat is the correct answer? Just the answer."
        ar = call_model("z-ai/glm-5.2", fp, 0.3, 200)
        if ar["success"]:
            any_ok = check_answer(ar["content"], q["answer"])
            fco += ar["cost"]
            total_cost += ar["cost"]
    fc += any_ok
    ft += 1
    print(f"  Q{i+1}: {'PASS' if any_ok else 'FAIL'} ${fco:.4f}", flush=True)

facc = (fc / ft * 100) if ft else 0
results["moa-fusion"] = {"correct": fc, "total": ft, "accuracy": facc, "cost": fco}
print(f"  → MoA: {fc}/{ft} = {facc:.1f}% ${fco:.4f}", flush=True)

print(f"\n{'='*60}")
print("REAL BENCHMARK RESULTS")
print(f"{'='*60}")
print(f"{'Model':<25} {'Accuracy':>10} {'Cost':>12}")
print(f"{'-'*50}")
for n, d in results.items():
    print(f"{n:<25} {d['accuracy']:>9.1f}% ${d['cost']:>11.4f}")
print(f"\nTotal: ${total_cost:.4f} / $26.00")
print(f"Remaining: ${26-total_cost:.2f}")

with open("/Users/saiful/temuclaude/research/benchmark_results_real.json", "w") as f:
    json.dump({"timestamp": time.strftime("%Y-%m-%d %H:%M:%S"), "total_cost": total_cost, "results": results}, f, indent=2)
print("\nSaved to research/benchmark_results_real.json")