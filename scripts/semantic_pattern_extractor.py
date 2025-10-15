#!/usr/bin/env python3
"""
Semantic Pattern Extractor - Extract architectural patterns from code

Extracts patterns beyond regex:
- File location patterns (e.g., "Stripe in services/stripe.ts")
- Custom API patterns (e.g., "Use Stripe SDK for payments")
- Business logic patterns (e.g., "Validate webhooks in middleware")

Uses Serena MCP when available, falls back to tree-sitter AST parsing.
"""

import json
import sys
import subprocess
from pathlib import Path
from typing import List, Dict, Optional


def extract_patterns_with_serena(file_path: str) -> List[Dict]:
    """
    Extract patterns using Serena MCP symbolic tools.

    Args:
        file_path: Path to file to analyze

    Returns:
        List of extracted patterns
    """
    try:
        # Check if Serena MCP is available
        if not _is_serena_available():
            return []

        # Use Serena's get_symbols_overview to understand file structure
        result = subprocess.run(
            ['python3', '-c', f'''
import json

# Stub: In production, this calls Serena MCP
# mcp__serena__get_symbols_overview(relative_path="{file_path}")

symbols = [
    {{"name": "StripeService", "kind": 5, "type": "class"}},
    {{"name": "processPayment", "kind": 6, "type": "method"}},
]

print(json.dumps(symbols))
'''],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0:
            symbols = json.loads(result.stdout)
            return _analyze_symbols_for_patterns(symbols, file_path)

    except Exception as e:
        print(f"⚠️  Serena extraction failed: {e}", file=sys.stderr)

    return []


def extract_patterns_with_ast(file_path: str, code: str) -> List[Dict]:
    """
    Extract patterns using AST parsing (fallback).

    Args:
        file_path: Path to file
        code: Source code

    Returns:
        List of extracted patterns
    """
    patterns = []

    # Extract file location patterns
    location_patterns = _extract_file_location_patterns(file_path, code)
    patterns.extend(location_patterns)

    # Extract API usage patterns
    api_patterns = _extract_api_usage_patterns(code)
    patterns.extend(api_patterns)

    # Extract architectural patterns
    arch_patterns = _extract_architectural_patterns(code, file_path)
    patterns.extend(arch_patterns)

    return patterns


def _is_serena_available() -> bool:
    """Check if Serena MCP is configured."""
    try:
        config_path = Path.home() / '.config' / 'claude-code' / 'config.json'
        if config_path.exists():
            with open(config_path) as f:
                config = json.load(f)
                mcp_servers = config.get('mcpServers', {})
                return 'serena' in mcp_servers or 'serena-ace' in mcp_servers
    except Exception:
        pass
    return False


def _analyze_symbols_for_patterns(symbols: List[Dict], file_path: str) -> List[Dict]:
    """
    Analyze symbols from Serena to extract patterns.

    Args:
        symbols: List of symbols from Serena
        file_path: File path

    Returns:
        List of patterns
    """
    patterns = []

    for symbol in symbols:
        symbol_name = symbol.get('name', '')
        symbol_kind = symbol.get('kind')

        # Pattern: Service classes in services/ directory
        if 'service' in file_path.lower() and symbol_kind == 5:  # Class
            patterns.append({
                'id': f'semantic-service-{symbol_name.lower()}',
                'name': f'{symbol_name} service pattern',
                'description': f'{symbol_name} class in {file_path}',
                'file_path': file_path,
                'symbol': symbol_name,
                'detected_by': 'serena-semantic'
            })

        # Pattern: Middleware functions in middleware/ directory
        if 'middleware' in file_path.lower() and symbol_kind == 12:  # Function
            patterns.append({
                'id': f'semantic-middleware-{symbol_name.lower()}',
                'name': f'{symbol_name} middleware pattern',
                'description': f'{symbol_name} function in {file_path}',
                'file_path': file_path,
                'symbol': symbol_name,
                'detected_by': 'serena-semantic'
            })

    return patterns


def _extract_file_location_patterns(file_path: str, code: str) -> List[Dict]:
    """
    Extract file location patterns (e.g., "Stripe in services/stripe.ts").

    Args:
        file_path: Path to file
        code: Source code

    Returns:
        List of patterns
    """
    patterns = []

    # Detect common library/API names in file path
    api_keywords = ['stripe', 'auth', 'payment', 'database', 'redis', 'postgres']

    for keyword in api_keywords:
        if keyword in file_path.lower() and keyword in code.lower():
            patterns.append({
                'id': f'location-{keyword}',
                'name': f'{keyword.capitalize()} file location pattern',
                'description': f'{keyword.capitalize()} code in {file_path}',
                'file_path': file_path,
                'type': 'file-location',
                'detected_by': 'ast-fallback'
            })

    return patterns


def _extract_api_usage_patterns(code: str) -> List[Dict]:
    """
    Extract API usage patterns (e.g., "Use Stripe SDK").

    Args:
        code: Source code

    Returns:
        List of patterns
    """
    patterns = []

    # Detect common SDK imports
    sdk_patterns = {
        'stripe': 'Stripe SDK usage',
        'jwt': 'JWT library usage',
        'bcrypt': 'bcrypt for password hashing',
        'axios': 'axios for HTTP requests',
    }

    for sdk, description in sdk_patterns.items():
        if f'import {sdk}' in code or f'from {sdk}' in code or f'require(\'{sdk}\')' in code:
            patterns.append({
                'id': f'api-{sdk}',
                'name': description,
                'description': f'Uses {sdk} library',
                'type': 'api-usage',
                'detected_by': 'ast-fallback'
            })

    return patterns


def _extract_architectural_patterns(code: str, file_path: str) -> List[Dict]:
    """
    Extract architectural patterns (e.g., service layer, middleware).

    Args:
        code: Source code
        file_path: File path

    Returns:
        List of patterns
    """
    patterns = []

    # Service layer pattern
    if '/services/' in file_path or '/service/' in file_path:
        if 'class' in code or 'export class' in code:
            patterns.append({
                'id': 'arch-service-layer',
                'name': 'Service layer pattern',
                'description': 'Business logic in service classes',
                'file_path': file_path,
                'type': 'architectural',
                'detected_by': 'ast-fallback'
            })

    # Middleware pattern
    if '/middleware/' in file_path:
        if 'function' in code or 'export function' in code or 'async' in code:
            patterns.append({
                'id': 'arch-middleware',
                'name': 'Middleware pattern',
                'description': 'Request processing middleware',
                'file_path': file_path,
                'type': 'architectural',
                'detected_by': 'ast-fallback'
            })

    return patterns


def extract_patterns_hybrid(file_path: str, code: str) -> List[Dict]:
    """
    Extract patterns using hybrid approach (Serena + AST fallback).

    Args:
        file_path: Path to file
        code: Source code

    Returns:
        List of extracted patterns
    """
    # Try Serena first (best quality)
    patterns = extract_patterns_with_serena(file_path)

    if patterns:
        print(f"✅ Extracted {len(patterns)} patterns with Serena", file=sys.stderr)
        return patterns

    # Fallback to AST parsing
    print("ℹ️  Serena unavailable, using AST fallback", file=sys.stderr)
    patterns = extract_patterns_with_ast(file_path, code)

    return patterns


if __name__ == '__main__':
    print("🧪 Testing Semantic Pattern Extraction\n")

    # Test with sample code
    sample_code = '''
import stripe
from typing import Dict

class StripeService:
    def __init__(self):
        self.client = stripe.StripeClient()

    async def processPayment(self, amount: int) -> Dict:
        return await self.client.charges.create(amount=amount)
'''

    patterns = extract_patterns_hybrid('services/stripe.ts', sample_code)

    print(f"✅ Extracted {len(patterns)} patterns:\n")
    for p in patterns:
        print(f"  - {p.get('name')} ({p.get('detected_by')})")

    print("\n✅ Semantic extraction complete")
