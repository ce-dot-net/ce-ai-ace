#!/usr/bin/env python3
"""
AgentEnd Hook - Analyze agent output for meta-learning

Learns from agent behavior to improve future performance.
"""

import json
import sys
from pathlib import Path

def analyze_agent_output():
    """Analyze agent output for patterns and insights."""
    try:
        # Read agent output from stdin
        input_data = json.load(sys.stdin)

        # Extract agent info
        agent_output = input_data.get('agent_output', '')
        agent_success = input_data.get('success', True)

        # Log for future meta-learning
        # (In production, this would analyze output and extract lessons)

        print(json.dumps({'continue': True}))
        print(f"ℹ️  Agent completed ({'success' if agent_success else 'failed'})", file=sys.stderr)

    except Exception as e:
        print(f"⚠️  Agent analysis failed: {e}", file=sys.stderr)
        print(json.dumps({'continue': True}))

if __name__ == '__main__':
    analyze_agent_output()
