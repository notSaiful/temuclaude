#!/usr/bin/env python3
"""
Research Daemon - Continuous deep research on priority topics.
Pulls findings from queue, runs deep research using LLM.
"""

import json
import time
import os
import sys
import subprocess
from pathlib import Path
from datetime import datetime, timezone

# Add research dir to path
sys.path.insert(0, "/Users/saiful/temuclaude/research")
sys.path.insert(0, "/Users/saiful/temuclaude/research/scripts")

from daemon_base import DaemonBase
from queue import pop_findings, push_implementation, push_raw_file
from dynamic_priorities import get_top_research_priorities

RESEARCH_DIR = Path("/Users/saiful/temuclaude/research")
FINDINGS_DIR = RESEARCH_DIR / "findings"
RAW_DIR = RESEARCH_DIR / "raw"


class ResearchDaemon(DaemonBase):
    """Continuous deep research daemon."""
    
    def __init__(self, daemon_id: int = 1):
        super().__init__(f"research_daemon_{daemon_id}")
        self.daemon_id = daemon_id
    
    def run_once(self) -> bool:
        """Research one topic from queue."""
        # Get current priorities
        priorities = get_top_research_priorities(10)
        if not priorities:
            self.logger.warning("No priorities available")
            return True
        
        top_topic, info = priorities[0]
        self.logger.info(f"Top priority: {top_topic} (score: {info['priority_score']})")
        
        # Check queue for findings to research
        findings = pop_findings(1)
        if not findings:
            # No findings, do proactive research on top priority
            self.logger.info(f"No findings in queue, researching priority: {top_topic}")
            self._research_topic(top_topic)
        else:
            for finding_file in findings:
                self.logger.info(f"Researching finding: {finding_file}")
                self._research_finding(finding_file)
        
        return True
    
    def _research_topic(self, topic: str):
        """Run deep research on a topic using LLM agent."""
        try:
            # Use the RANK 1 research agent prompt via cron job approach
            # but run it directly here
            prompt = f"""You are the RANK 1 research agent for Temuclaude. Research this topic deeply: {topic}

Focus on:
1. Latest papers, repos, implementations
2. Concrete techniques we can implement
3. Code examples, APIs, integration details
4. Benchmarks, results, tradeoffs

Output a deep research report as markdown to: {FINDINGS_DIR}/deep_research_{topic}_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')}.md

Include:
- Executive summary
- Key techniques with implementation details
- Code snippets / pseudo-code
- Integration points for Temuclaude
- Risk assessment
- Priority: implement now / track for future / blocked
"""
            
            # Write prompt to file for LLM to process
            prompt_file = RAW_DIR / f"research_prompt_{topic}_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')}.txt"
            with open(prompt_file, 'w') as f:
                f.write(prompt)
            
            self.logger.info(f"Created research prompt: {prompt_file}")
            
        except Exception as e:
            self.logger.exception(f"Research failed for {topic}: {e}")
    
    def _research_finding(self, finding_file: str):
        """Deep research on a specific finding file."""
        try:
            with open(finding_file) as f:
                finding = json.load(f)
            
            title = finding.get('title', finding.get('name', 'unknown'))
            self.logger.info(f"Deep research on: {title}")
            
            # Create research output
            timestamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')
            output_file = FINDINGS_DIR / f"deep_research_{title.replace(' ', '_')[:50]}_{timestamp}.md"
            
            # For now, create a structured research template
            # The actual LLM research would be triggered via the cron agent system
            report = f"""# Deep Research: {title}

## Source Finding
- File: {finding_file}
- Type: {finding.get('type', 'unknown')}
- Relevance Score: {finding.get('relevance_score', 'N/A')}
- Keywords: {finding.get('matched_keywords', [])}

## Research Status
- Status: QUEUED_FOR_LLM_RESEARCH
- Priority: HIGH
- Timestamp: {datetime.now(timezone.utc).isoformat()}

## Next Steps
1. LLM agent reads this finding
2. Conducts deep web/paper search
3. Produces implementation-ready report
4. Queues for auto-integrator
"""
            with open(output_file, 'w') as f:
                f.write(report)
            
            # Push to implementation queue
            push_implementation([str(output_file)])
            self.logger.info(f"Research report created: {output_file}")
            
        except Exception as e:
            self.logger.exception(f"Failed to process finding {finding_file}: {e}")


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--id", type=int, default=1)
    args = parser.parse_args()
    
    daemon = ResearchDaemon(args.id)
    # Research every 5 minutes
    daemon.run(interval=300)


if __name__ == "__main__":
    main()