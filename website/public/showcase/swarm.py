import time
import json
from openai import OpenAI

# Configuration
API_BASE_URL = "https://saifulbusiness47--temuclaude-serve.modal.run/v1"
MODEL = "temuclaude"
API_KEY = "tc_eval_master_2026"
COST_PER_M_TOKENS = 1.44
TOPIC = "The future of AI orchestration and multi-model systems"
MAX_RETRIES = 3
RETRY_DELAY = 2

# Initialize OpenAI client with custom base_url
client = OpenAI(
    api_key=API_KEY,
    base_url=API_BASE_URL,
)

def call_agent(system_prompt, user_prompt, agent_name):
    """Call the LLM with retries and error handling. Returns (response_text, prompt_tokens, completion_tokens, elapsed)."""
    last_error = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            start = time.time()
            response = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.7,
            )
            elapsed = time.time() - start
            content = response.choices[0].message.content or ""
            usage = response.usage
            prompt_tokens = usage.prompt_tokens if usage else 0
            completion_tokens = usage.completion_tokens if usage else 0
            return content, prompt_tokens, completion_tokens, elapsed
        except Exception as e:
            last_error = e
            print(f"[{agent_name}] Attempt {attempt}/{MAX_RETRIES} failed: {e}")
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY * attempt)
    raise RuntimeError(f"[{agent_name}] All retries exhausted. Last error: {last_error}")


def run_research_swarm(topic):
    print("=" * 80)
    print("  MULTI-AGENT RESEARCH SWARM")
    print("=" * 80)
    print(f"Topic: {topic}")
    print(f"Model: {MODEL}")
    print(f"Endpoint: {API_BASE_URL}/chat/completions")
    print(f"Cost: ${COST_PER_M_TOKENS}/M tokens")
    print("=" * 80)
    print()

    total_prompt_tokens = 0
    total_completion_tokens = 0
    swarm_start = time.time()

    # ------------------------------------------------------------------
    # Agent 1: Researcher
    # ------------------------------------------------------------------
    researcher_system = (
        "You are a Researcher agent. Your job is to gather comprehensive, factual "
        "information on the given topic. Provide key facts, trends, notable players, "
        "technologies, and references. Structure your findings with clear bullet points "
        "and sections. Be thorough and objective."
    )
    researcher_user = (
        f"Research the following topic thoroughly:\n\nTopic: {topic}\n\n"
        "Provide a comprehensive overview including:\n"
        "1. Current state of the field\n"
        "2. Key technologies and frameworks\n"
        "3. Major players and projects\n"
        "4. Recent developments\n"
        "5. Open challenges\n"
    )

    print("[Researcher] Gathering information...")
    research_output, r_pt, r_ct, r_time = call_agent(
        researcher_system, researcher_user, "Researcher"
    )
    total_prompt_tokens += r_pt
    total_completion_tokens += r_ct

    print()
    print("-" * 80)
    print("  AGENT 1: RESEARCHER OUTPUT")
    print("-" * 80)
    print(research_output)
    print()
    print(f"[Researcher] Tokens - Prompt: {r_pt}, Completion: {r_ct}, Total: {r_pt + r_ct}")
    print(f"[Researcher] Time: {r_time:.2f}s")
    print()

    # ------------------------------------------------------------------
    # Agent 2: Analyzer
    # ------------------------------------------------------------------
    analyzer_system = (
        "You are an Analyzer agent. You review research findings and extract deep "
        "insights, patterns, risks, and strategic implications. You identify gaps, "
        "contradictions, and opportunities. Provide structured analysis with clear "
        "reasoning."
    )
    analyzer_user = (
        f"Analyze the following research findings on the topic: {topic}\n\n"
        f"Research findings:\n{research_output}\n\n"
        "Provide your analysis covering:\n"
        "1. Key insights and patterns\n"
        "2. Critical risks and challenges\n"
        "3. Strategic opportunities\n"
        "4. Gaps in current approaches\n"
        "5. Predictions for the next 2-3 years\n"
    )

    print("[Analyzer] Reviewing and extracting insights...")
    analysis_output, a_pt, a_ct, a_time = call_agent(
        analyzer_system, analyzer_user, "Analyzer"
    )
    total_prompt_tokens += a_pt
    total_completion_tokens += a_ct

    print()
    print("-" * 80)
    print("  AGENT 2: ANALYZER OUTPUT")
    print("-" * 80)
    print(analysis_output)
    print()
    print(f"[Analyzer] Tokens - Prompt: {a_pt}, Completion: {a_ct}, Total: {a_pt + a_ct}")
    print(f"[Analyzer] Time: {a_time:.2f}s")
    print()

    # ------------------------------------------------------------------
    # Agent 3: Writer
    # ------------------------------------------------------------------
    writer_system = (
        "You are a Writer agent. You synthesize research and analysis into a clear, "
        "well-structured, professional report. Use headings, subheadings, and "
        "narrative flow. Make it engaging yet authoritative. Include an executive "
        "summary and a conclusion with recommendations."
    )
    writer_user = (
        f"Write a comprehensive professional report on the topic: {topic}\n\n"
        f"Use the following research findings:\n{research_output}\n\n"
        f"And the following analysis:\n{analysis_output}\n\n"
        "Structure the report as:\n"
        "1. Executive Summary\n"
        "2. Introduction\n"
        "3. Current Landscape\n"
        "4. Key Findings and Analysis\n"
        "5. Future Outlook\n"
        "6. Recommendations\n"
        "7. Conclusion\n"
    )

    print("[Writer] Synthesizing final report...")
    writer_output, w_pt, w_ct, w_time = call_agent(
        writer_system, writer_user, "Writer"
    )
    total_prompt_tokens += w_pt
    total_completion_tokens += w_ct

    print()
    print("-" * 80)
    print("  AGENT 3: WRITER OUTPUT (FINAL REPORT)")
    print("-" * 80)
    print(writer_output)
    print()
    print(f"[Writer] Tokens - Prompt: {w_pt}, Completion: {w_ct}, Total: {w_pt + w_ct}")
    print(f"[Writer] Time: {w_time:.2f}s")
    print()

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    swarm_elapsed = time.time() - swarm_start
    total_tokens = total_prompt_tokens + total_completion_tokens
    total_cost = (total_tokens / 1_000_000) * COST_PER_M_TOKENS

    print("=" * 80)
    print("  SWARM SUMMARY")
    print("=" * 80)
    print(f"{'Agent':<15} {'Prompt Tokens':<18} {'Completion Tokens':<20} {'Total Tokens':<15} {'Time (s)':<10}")
    print("-" * 80)
    print(f"{'Researcher':<15} {r_pt:<18} {r_ct:<20} {r_pt + r_ct:<15} {r_time:<10.2f}")
    print(f"{'Analyzer':<15} {a_pt:<18} {a_ct:<20} {a_pt + a_ct:<15} {a_time:<10.2f}")
    print(f"{'Writer':<15} {w_pt:<18} {w_ct:<20} {w_pt + w_ct:<15} {w_time:<10.2f}")
    print("-" * 80)
    print(f"{'TOTAL':<15} {total_prompt_tokens:<18} {total_completion_tokens:<20} {total_tokens:<15} {swarm_elapsed:<10.2f}")
    print()
    print(f"Total Tokens Used:   {total_tokens:,}")
    print(f"Total Cost:          ${total_cost:.6f}")
    print(f"Total Elapsed Time:  {swarm_elapsed:.2f}s")
    print(f"Cost Rate:           ${COST_PER_M_TOKENS}/M tokens")
    print("=" * 80)


if __name__ == "__main__":
    try:
        run_research_swarm(TOPIC)
    except Exception as e:
        print(f"\nFATAL ERROR: Research swarm failed: {e}")
        raise