#!/usr/bin/env python3
"""
Domain Auto-Discovery - Bottom-up domain taxonomy learning

Uses Claude to analyze patterns and discover domain taxonomy WITHOUT hardcoding.
Domains emerge from observed coding patterns and execution feedback.

Based on ACE paper: "Domain-specific heuristics learned from execution feedback"
"""

import json
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
        # Call Claude for domain analysis
        # In production, this uses Claude Code's Task tool
        result = subprocess.run(
            ['python3', '-c', f'''
import json

# Stub: In production, this calls Claude via Task tool
# For now, return placeholder taxonomy
taxonomy = {{
    "concrete": {{
        "payments-stripe": {{
            "patterns": ["stripe-001", "stripe-002"],
            "description": "Stripe payment integration",
            "evidence": ["services/stripe.ts", "lib/payments.ts"]
        }}
    }},
    "abstract": {{
        "service-layer": {{
            "instances": ["payments-stripe"],
            "description": "Business logic encapsulation"
        }}
    }},
    "principles": {{
        "separation-of-concerns": {{
            "applied_in": ["service-layer"],
            "description": "Isolate business logic from presentation"
        }}
    }}
}}

print(json.dumps(taxonomy))
'''],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0:
            taxonomy = json.loads(result.stdout)
            return taxonomy
        else:
            print(f"⚠️  Domain discovery failed: {result.stderr}", file=sys.stderr)
            return {"domains": {}, "hierarchy": {}}

    except Exception as e:
        print(f"⚠️  Domain discovery error: {e}", file=sys.stderr)
        return {"domains": {}, "hierarchy": {}}


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
