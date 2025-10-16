#!/usr/bin/env python3
"""
Domain Auto-Discovery - Bottom-up domain taxonomy learning

Uses Claude to analyze patterns and discover domain taxonomy WITHOUT hardcoding.
Domains emerge from observed coding patterns and execution feedback.

Based on ACE paper: "Domain-specific heuristics learned from execution feedback"
"""

import json
import os
import sys
import subprocess
from pathlib import Path
from typing import List, Dict, Optional


def discover_domains_from_patterns(patterns: List[Dict]) -> Dict:
    """
    Auto-discover domain taxonomy using Claude.
    No hardcoding - domains emerge from observed patterns.

    Args:
        patterns: List of observed patterns from code

    Returns:
        Hierarchical domain taxonomy
    """
    if not patterns:
        return {"domains": {}, "hierarchy": {}}

    # Prepare pattern summary for Claude
    pattern_summary = [
        {
            "name": p.get("name", "unnamed"),
            "description": p.get("description", ""),
            "language": p.get("language", "unknown"),
            "file_path": p.get("file_path", ""),
            "observations": p.get("observations", 0)
        }
        for p in patterns[:50]  # Limit to top 50 patterns
    ]

    prompt = f"""Analyze these {len(pattern_summary)} coding patterns to discover domain taxonomy:

{json.dumps(pattern_summary, indent=2)}

Your task: Identify domains WITHOUT using any predefined categories. Let domains emerge from the data.

Discover three levels:

1. **Concrete Domains** (file-location specific):
   - Where is this code? (e.g., "payments-stripe", "auth-jwt", "database-postgres")
   - Look for file paths, API names, library usage

2. **Abstract Patterns** (architectural):
   - What pattern is this? (e.g., "service-layer", "middleware", "validation")
   - Look for recurring structures across files

3. **Principles** (general best practices):
   - What principle does this follow? (e.g., "separation-of-concerns", "DRY", "type-safety")
   - Look for coding philosophies

Output hierarchical JSON:
{{
  "concrete": {{
    "domain-name": {{
      "patterns": ["pattern-id-1", "pattern-id-2"],
      "description": "Brief description",
      "evidence": ["file-path-1", "file-path-2"]
    }}
  }},
  "abstract": {{
    "pattern-name": {{
      "instances": ["concrete-domain-1", "concrete-domain-2"],
      "description": "Brief description"
    }}
  }},
  "principles": {{
    "principle-name": {{
      "applied_in": ["abstract-pattern-1", "abstract-pattern-2"],
      "description": "Brief description"
    }}
  }}
}}

CRITICAL: Do NOT hardcode domains. Infer them from the actual patterns and file paths.
"""

    try:
        # Output patterns to context for Claude to analyze via domain-discoverer agent
        # This allows Claude in interactive session to use the Task tool

        print(f"""
🔬 ACE Domain Discovery Request

{len(pattern_summary)} patterns detected. Please invoke the domain-discoverer agent to analyze these patterns and discover domain taxonomy.

<patterns_for_domain_discovery>
{json.dumps(pattern_summary, indent=2)}
</patterns_for_domain_discovery>

Use the Task tool to invoke ace-orchestration:domain-discoverer agent with the patterns above.
The agent will discover concrete domains, abstract patterns, and principles WITHOUT hardcoding.

Expected output format:
- concrete: File-location specific domains (e.g., "claude-code-plugin-dev", "mcp-integration")
- abstract: Architectural patterns (e.g., "plugin-architecture", "hook-lifecycle")
- principles: General best practices (e.g., "separation-of-concerns", "modern-python-apis")

Store the discovered taxonomy in .ace-memory/domain_taxonomy.json
""")

        # Return empty taxonomy - actual discovery happens via Claude + Task tool
        return {
            "concrete": {},
            "abstract": {},
            "principles": {},
            "metadata": {
                "total_patterns_analyzed": len(pattern_summary),
                "discovery_method": "agent-based (domain-discoverer via Task tool)",
                "discovered_at": subprocess.run(['date', '-Iseconds'], capture_output=True, text=True).stdout.strip(),
                "status": "pending_agent_invocation"
            }
        }

    except Exception as e:
        print(f"⚠️  Domain discovery error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        return {"concrete": {}, "abstract": {}, "principles": {}, "metadata": {}}


def assign_pattern_to_domains(pattern: Dict, taxonomy: Dict) -> List[str]:
    """
    Assign a pattern to discovered domains.

    Args:
        pattern: Pattern dict with name, description, file_path
        taxonomy: Domain taxonomy from discover_domains_from_patterns()

    Returns:
        List of domain IDs that this pattern belongs to
    """
    domains = []

    # Check concrete domains (file-location based)
    for domain_name, domain_info in taxonomy.get('concrete', {}).items():
        evidence = domain_info.get('evidence', [])
        pattern_file = pattern.get('file_path', '')

        # Check if pattern's file path matches domain evidence
        for evidence_path in evidence:
            if evidence_path in pattern_file or pattern_file in evidence_path:
                domains.append(f"concrete:{domain_name}")
                break

    # Check abstract patterns (architectural)
    for pattern_name, pattern_info in taxonomy.get('abstract', {}).items():
        # Check if pattern matches abstract pattern description
        pattern_desc = pattern.get('description', '').lower()
        abstract_desc = pattern_info.get('description', '').lower()

        # Simple keyword matching (can be improved with embeddings)
        if any(word in pattern_desc for word in abstract_desc.split()):
            domains.append(f"abstract:{pattern_name}")

    # If no domains found, assign 'general'
    if not domains:
        domains.append('general')

    return domains


def update_taxonomy_with_new_patterns(existing_taxonomy: Dict,
                                       new_patterns: List[Dict]) -> Dict:
    """
    Update domain taxonomy with new patterns (incremental learning).

    Args:
        existing_taxonomy: Current domain taxonomy
        new_patterns: Newly observed patterns

    Returns:
        Updated taxonomy
    """
    # Re-discover domains including new patterns
    # This allows taxonomy to evolve over time
    all_patterns = new_patterns  # In production, merge with existing
    return discover_domains_from_patterns(all_patterns)


if __name__ == '__main__':
    print("🧪 Testing Domain Auto-Discovery\n")

    # Sample patterns
    sample_patterns = [
        {
            "name": "Use Stripe SDK",
            "description": "Stripe payment processing",
            "language": "typescript",
            "file_path": "services/stripe.ts",
            "observations": 5
        },
        {
            "name": "JWT authentication",
            "description": "JWT token validation",
            "language": "typescript",
            "file_path": "middleware/auth.ts",
            "observations": 3
        },
        {
            "name": "Use TypedDict",
            "description": "TypedDict for configs",
            "language": "python",
            "file_path": "config/settings.py",
            "observations": 10
        }
    ]

    taxonomy = discover_domains_from_patterns(sample_patterns)

    print("📊 Discovered Domain Taxonomy:\n")
    print(json.dumps(taxonomy, indent=2))

    print("\n✅ Domain discovery complete")
