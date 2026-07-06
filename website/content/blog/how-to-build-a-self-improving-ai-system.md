# How to build a self-improving AI system with Temuclaude

Welcome to this technical tutorial on building a self-improving AI system using **Temuclaude**. Temuclaude is a lightweight Python framework designed to interface with Anthropic’s Claude API, enabling developers to create autonomous feedback loops. By evaluating its own outputs against strict criteria, the AI iteratively refines its responses—whether they are code snippets, text, or architectural designs—until it meets a defined success threshold.

## Prerequisites

Before we begin, ensure you have the following:
* Python 3.8 or higher
* An Anthropic API key
* Basic understanding of Python and prompt engineering

## Step 1: Installation & Setup

First, install the Temuclaude package via pip. Open your terminal and run:

```bash
pip install temuclaude
```

Next, set your Anthropic API key as an environment variable so the framework can authenticate your requests:

```bash
export ANTHROPIC_API_KEY="your_api_key_here"
```

## Step 2: Initialize the Temuclaude Engine

Create a new Python file named `self_improving_ai.py`. We will start by importing the necessary classes from Temuclaude and initializing our core agent.

```python
from temuclaude import Agent, Evaluator

# Initialize the core agent using Claude 3 Opus
agent = Agent(model="claude-3-opus-20240229", temperature=0.7)
```

## Step 3: Define the Task and Evaluation Criteria

A self-improving system needs a clear goal and a way to measure success. Let's define a coding task and the specific criteria the AI must meet.

```python
task = "Write a Python function to calculate the nth Fibonacci number."
criteria = """
1. The code must run in O(n) time complexity.
2. It must include Python type hints.
3. It must handle edge cases (e.g., n <= 0).
"""

# Initialize the evaluator with our success criteria
evaluator = Evaluator(criteria=criteria)
```

## Step 4: Implement the Self-Improvement Loop

The core of Temuclaude is the feedback loop. The agent generates an initial output, the evaluator critiques it, and the agent rewrites the output based on the feedback. 

Add the following function to your script:

```python
def self_improve(agent, evaluator, task, max_iterations=3):
    # Generate the initial attempt
    current_output = agent.generate(f"Task: {task}")
    
    for i in range(max_iterations):
        print(f"\n--- Iteration {i+1} ---")
        print(current_output)
        
        # Evaluate the current output against the criteria
        evaluation = evaluator.evaluate(current_output)
        print("\n[Evaluator Feedback]:", evaluation.get('comments'))
        
        # Check if the output is optimal
        if evaluation.get('is_optimal'):
            print("\n✅ Optimal solution reached!")
            return current_output
            
        # Construct the improvement prompt
        improvement_prompt = f"""
        Previous output:
        {current_output}
        
        Feedback:
        {evaluation.get('comments')}
        
        Original Task:
        {task}
        
        Please rewrite the output to fully address the feedback and meet all criteria.
        """
        
        # Generate the improved output
        current_output = agent.generate(improvement_prompt)
        
    print("\n⚠️ Max iterations reached. Returning latest version.")
    return current_output
```

## Step 5: Run the System

Finally, add the execution block to run your self-improving loop. 

```python
if __name__ == "__main__":
    print("Starting self-improving AI system...")
    final_code = self_improve(agent, evaluator, task, max_iterations=3)
    
    print("\n=== Final Optimized Output ===")
    print(final_code)
```

Run the script in your terminal:

```bash
python self_improving_ai.py
```

## Conclusion

You have successfully built a self-improving AI system using Temuclaude. By combining the `Agent` for generation and the `Evaluator` for critique, you've created an autonomous loop that refines its own output. You can extend this system by integrating actual unit tests into the `Evaluator` class, allowing the AI to run code, read stack traces, and debug its own software autonomously.