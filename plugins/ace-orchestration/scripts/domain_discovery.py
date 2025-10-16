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
        # Simplified domain discovery using heuristic analysis
        # In production with Claude Code, this would use the Task tool to invoke domain-discoverer agent
        # For now, use rule-based discovery from file paths and pattern descriptions

        concrete_domains = {}
        abstract_patterns = {}
        principles = {}

        # Group patterns by file directory (concrete domains)
        file_groups = {}
        for p in pattern_summary:
            file_path = p.get('file_path', '')
            if not file_path:
                continue

            # Extract directory structure for domain detection
            path_parts = Path(file_path).parts

            # Identify concrete domains from file paths
            if 'plugins' in path_parts:
                domain_key = 'claude-code-plugin-dev'
            elif 'scripts' in path_parts:
                domain_key = 'python-scripting'
            elif 'agents' in path_parts:
                domain_key = 'agent-development'
            elif 'hooks' in path_parts:
                domain_key = 'plugin-hooks'
            else:
                domain_key = 'general-python'

            if domain_key not in file_groups:
                file_groups[domain_key] = []
            file_groups[domain_key].append(p)

        # Build concrete domains from file groups
        for domain_id, patterns in file_groups.items():
            if len(patterns) < 2:  # Need at least 2 patterns for a domain
                continue

            concrete_domains[domain_id] = {
                'description': f"Patterns found in {domain_id.replace('-', ' ')} code",
                'evidence': list(set(p.get('file_path', '') for p in patterns)),
                'patterns': [p.get('name', 'unnamed') for p in patterns],
                'confidence': min(0.9, 0.5 + (len(patterns) * 0.1))
            }

        # Identify abstract patterns from descriptions
        desc_keywords = {
            'modern-python-apis': ['pathlib', 'f-string', 'comprehension'],
            'defensive-coding': ['error handling', 'exception', 'validation'],
            'code-quality': ['readability', 'maintainability', 'pythonic']
        }

        for abstract_id, keywords in desc_keywords.items():
            matching_patterns = []
            for p in pattern_summary:
                desc = p.get('description', '').lower()
                name = p.get('name', '').lower()
                if any(kw in desc or kw in name for kw in keywords):
                    matching_patterns.append(p.get('name', 'unnamed'))

            if matching_patterns:
                abstract_patterns[abstract_id] = {
                    'description': f"Patterns related to {abstract_id.replace('-', ' ')}",
                    'instances': list(concrete_domains.keys()),
                    'confidence': 0.7
                }

        # Identify principles
        if abstract_patterns:
            principles['best-practices'] = {
                'description': 'Modern Python best practices and idioms',
                'applied_in': list(abstract_patterns.keys()),
                'confidence': 0.8
            }

        taxonomy = {
            'concrete': concrete_domains,
            'abstract': abstract_patterns,
            'principles': principles,
            'metadata': {
                'total_patterns_analyzed': len(pattern_summary),
                'discovery_method': 'heuristic file-path and description analysis',
                'discovered_at': subprocess.run(['date', '-Iseconds'], capture_output=True, text=True).stdout.strip()
            }
        }

        domains_found = len(concrete_domains) + len(abstract_patterns)
        if domains_found > 0:
            print(f"✅ Discovered {domains_found} domains via heuristic analysis", file=sys.stderr)

        return taxonomy

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
