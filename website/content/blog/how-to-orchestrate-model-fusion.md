# How to orchestrate model fusion with Temuclaude

Model fusion is an advanced technique that combines the outputs or internal representations of multiple Large Language Models (LLMs) to create a more robust, accurate, and nuanced final response. **Temuclaude** is a lightweight Python orchestration framework designed specifically to fuse Claude-based models and other compatible architectures. 

This tutorial will guide you through setting up a Temuclaude pipeline to orchestrate output-level fusion across multiple models.

## Prerequisites

Before you begin, ensure you have the following:
* Python 3.9 or higher
* API keys for the models you intend to fuse (e.g., Anthropic, OpenAI)
* Basic understanding of Python and LLM APIs

## Step 1: Installation and Environment Setup

First, install the Temuclaude package via pip. It includes the core orchestration engine and built-in adapters for popular LLM providers.

```bash
pip install temuclaude
```

Next, set up your environment variables. Temuclaude reads these automatically to authenticate API requests.

```bash
export ANTHROPIC_API_KEY="your_anthropic_key"
export OPENAI_API_KEY="your_openai_key"
```

## Step 2: Define the Base Models

In Temuclaude, you define the models you want to fuse as a list of `ModelNode` objects. Each node wraps a specific model configuration. In this example, we will fuse Claude 3 Opus (for deep reasoning) with Claude 3 Haiku (for rapid, concise generation).

Create a file named `fusion_pipeline.py` and add the following:

```python
from temuclaude.models import ModelNode

# Define the primary reasoning model
opus_node = ModelNode(
    model_id="claude-3-opus-20240229",
    role="reasoner",
    temperature=0.2,
    max_tokens=1024
)

# Define the secondary fast model
haiku_node = ModelNode(
    model_id="claude-3-haiku-20240307",
    role="summarizer",
    temperature=0.5,
    max_tokens=512
)

model_pool = [opus_node, haiku_node]
```

## Step 3: Configure the Fusion Strategy

Temuclaude supports several fusion strategies, such as `WeightedVoting`, `LogitAveraging`, and `SequentialSynthesis`. For this tutorial, we will use `SequentialSynthesis`, where the "reasoner" generates the initial draft, and the "summarizer" refines and fuses its own output with the reasoner's draft.

```python
from temuclaude.fusion import SequentialSynthesis

# Initialize the fusion strategy
fusion_strategy = SequentialSynthesis(
    models=model_pool,
    synthesis_prompt="Combine the following outputs into a single, highly accurate and concise response. Resolve any contradictions by favoring the 'reasoner' output."
)
```

## Step 4: Execute the Orchestration Pipeline

Now, instantiate the `TemuclaudeOrchestrator` with your fusion strategy and execute a prompt. The orchestrator handles the parallel or sequential API calls, passes the intermediate outputs through the fusion strategy, and returns the final unified response.

```python
from temuclaude.orchestrator import TemuclaudeOrchestrator

# Initialize the orchestrator
orchestrator = TemuclaudeOrchestrator(strategy=fusion_strategy)

# Define your prompt
user_prompt = "Explain the implications of quantum entanglement on modern cryptography."

# Run the fusion pipeline
print("Orchestrating model fusion...")
final_output = orchestrator.run(prompt=user_prompt)

print("\n--- Fused Output ---")
print(final_output)
```

## Step 5: Run the Script

Execute your Python script from the terminal to see the fused output in action.

```bash
python fusion_pipeline.py
```

The orchestrator will first query Opus for a detailed explanation, then query Haiku for a concise summary. Finally, it will use the `synthesis_prompt` to fuse the two outputs, returning a response that balances deep technical accuracy with concise readability.

## Conclusion

Temuclaude simplifies the complex process of LLM orchestration. By defining `ModelNode` objects, selecting a fusion strategy like `SequentialSynthesis`, and utilizing the `TemuclaudeOrchestrator`, you can easily combine the unique strengths of multiple models. Experiment with different models, temperatures, and fusion strategies to find the optimal configuration for your specific use case.