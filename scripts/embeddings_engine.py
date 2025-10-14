#!/usr/bin/env python3
"""
Semantic Embeddings Engine - ACE Phase 3

Implements semantic similarity as per ACE paper:
"Uses semantic embeddings (not just string matching)"
"Deduplicate with cosine similarity > 0.85 on sentence embeddings"

Supports multiple backends:
1. OpenAI embeddings API (preferred)
2. Local sentence-transformers (fallback)
3. Enhanced string similarity (last resort)
"""

import os
import sys
import json
import hashlib
from pathlib import Path
from typing import List, Tuple, Optional
import math

PROJECT_ROOT = Path.cwd()
EMBEDDINGS_CACHE = PROJECT_ROOT / '.ace-memory' / 'embeddings-cache.json'

# Cache for embeddings to avoid re-computing
_embeddings_cache = None

def load_cache() -> dict:
    """Load embeddings cache from disk."""
    global _embeddings_cache
    if _embeddings_cache is not None:
        return _embeddings_cache

    if EMBEDDINGS_CACHE.exists():
        try:
            with open(EMBEDDINGS_CACHE, 'r') as f:
                _embeddings_cache = json.load(f)
                return _embeddings_cache
        except:
            pass

    _embeddings_cache = {}
    return _embeddings_cache

def save_cache(cache: dict):
    """Save embeddings cache to disk."""
    EMBEDDINGS_CACHE.parent.mkdir(parents=True, exist_ok=True)
    with open(EMBEDDINGS_CACHE, 'w') as f:
        json.dump(cache, f, indent=2)

def text_to_key(text: str) -> str:
    """Generate cache key from text."""
    return hashlib.md5(text.encode()).hexdigest()

def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Compute cosine similarity between two vectors."""
    if len(vec1) != len(vec2):
        return 0.0

    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    magnitude1 = math.sqrt(sum(a * a for a in vec1))
    magnitude2 = math.sqrt(sum(b * b for b in vec2))

    if magnitude1 == 0 or magnitude2 == 0:
        return 0.0

    return dot_product / (magnitude1 * magnitude2)

# ============================================================================
# Backend 1: OpenAI Embeddings (preferred)
# ============================================================================

def get_openai_embedding(text: str) -> Optional[List[float]]:
    """
    Get embedding from OpenAI API.

    Requires OPENAI_API_KEY environment variable.
    """
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        return None

    try:
        import urllib.request
        import urllib.error

        # Use OpenAI embeddings API
        url = 'https://api.openai.com/v1/embeddings'
        data = json.dumps({
            'input': text,
            'model': 'text-embedding-3-small'  # Fast, cheap, good quality
        }).encode('utf-8')

        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }

        request = urllib.request.Request(url, data=data, headers=headers)
        response = urllib.request.urlopen(request, timeout=10)
        result = json.loads(response.read().decode())

        embedding = result['data'][0]['embedding']
        return embedding

    except Exception as e:
        print(f"⚠️  OpenAI embeddings failed: {e}", file=sys.stderr)
        return None

# ============================================================================
# Backend 2: Local sentence-transformers (fallback)
# ============================================================================

_sentence_transformer_model = None

def get_local_embedding(text: str) -> Optional[List[float]]:
    """
    Get embedding using local sentence-transformers.

    Requires: pip install sentence-transformers
    """
    global _sentence_transformer_model

    try:
        if _sentence_transformer_model is None:
            from sentence_transformers import SentenceTransformer
            # Use small, fast model
            _sentence_transformer_model = SentenceTransformer('all-MiniLM-L6-v2')

        embedding = _sentence_transformer_model.encode(text)
        return embedding.tolist()

    except ImportError:
        # sentence-transformers not installed
        return None
    except Exception as e:
        print(f"⚠️  Local embeddings failed: {e}", file=sys.stderr)
        return None

# ============================================================================
# Backend 3: Enhanced string similarity (last resort)
# ============================================================================

def get_string_similarity_vector(text: str) -> List[float]:
    """
    Generate pseudo-embedding from text features.

    Better than simple Jaccard, but not as good as real embeddings.
    """
    # Extract features
    words = text.lower().split()
    unique_words = set(words)

    # Feature vector (100 dimensions)
    features = [
        len(words),                          # Length
        len(unique_words),                   # Vocabulary size
        len(unique_words) / max(len(words), 1),  # Uniqueness ratio
        sum(len(w) for w in words) / max(len(words), 1),  # Avg word length
    ]

    # Add word presence features (simple bag-of-words)
    # Hash words into 96 buckets
    for word in unique_words:
        bucket = hash(word) % 96
        if len(features) <= bucket + 4:
            features.extend([0.0] * (bucket + 5 - len(features)))
        features[bucket + 4] += 1.0

    # Normalize to 100 dimensions
    while len(features) < 100:
        features.append(0.0)
    features = features[:100]

    # L2 normalize
    magnitude = math.sqrt(sum(f * f for f in features))
    if magnitude > 0:
        features = [f / magnitude for f in features]

    return features

# ============================================================================
# Main API
# ============================================================================

def get_embedding(text: str, use_cache: bool = True) -> List[float]:
    """
    Get embedding for text using best available backend.

    Priority:
    1. OpenAI API (if OPENAI_API_KEY set)
    2. Local sentence-transformers (if installed)
    3. Enhanced string features (always available)

    Args:
        text: Text to embed
        use_cache: Use cached embeddings if available

    Returns:
        Embedding vector (list of floats)
    """
    # Check cache
    if use_cache:
        cache = load_cache()
        key = text_to_key(text)
        if key in cache:
            return cache[key]

    # Try backends in order
    embedding = None

    # 1. OpenAI
    embedding = get_openai_embedding(text)
    if embedding:
        # Cache it
        if use_cache:
            cache = load_cache()
            cache[text_to_key(text)] = embedding
            save_cache(cache)
        return embedding

    # 2. Local
    embedding = get_local_embedding(text)
    if embedding:
        # Cache it
        if use_cache:
            cache = load_cache()
            cache[text_to_key(text)] = embedding
            save_cache(cache)
        return embedding

    # 3. Fallback
    embedding = get_string_similarity_vector(text)

    # Cache it
    if use_cache:
        cache = load_cache()
        cache[text_to_key(text)] = embedding
        save_cache(cache)

    return embedding

def calculate_semantic_similarity(text1: str, text2: str) -> float:
    """
    Calculate semantic similarity between two texts.

    Returns:
        Similarity score between 0.0 and 1.0
    """
    emb1 = get_embedding(text1)
    emb2 = get_embedding(text2)

    return cosine_similarity(emb1, emb2)

def find_similar_patterns(
    query_text: str,
    candidate_texts: List[str],
    threshold: float = 0.85
) -> List[Tuple[int, float]]:
    """
    Find patterns similar to query above threshold.

    Args:
        query_text: Text to compare against
        candidate_texts: List of candidate texts
        threshold: Minimum similarity (default 0.85 from ACE paper)

    Returns:
        List of (index, similarity) tuples for matches above threshold
    """
    query_emb = get_embedding(query_text)
    matches = []

    for i, candidate in enumerate(candidate_texts):
        candidate_emb = get_embedding(candidate)
        similarity = cosine_similarity(query_emb, candidate_emb)

        if similarity >= threshold:
            matches.append((i, similarity))

    # Sort by similarity (descending)
    matches.sort(key=lambda x: x[1], reverse=True)

    return matches

def get_backend_info() -> dict:
    """Get information about available embedding backends."""
    info = {
        'openai': bool(os.getenv('OPENAI_API_KEY')),
        'local': False,
        'fallback': True
    }

    try:
        import sentence_transformers
        info['local'] = True
    except ImportError:
        pass

    return info

# ============================================================================
# CLI for testing
# ============================================================================

if __name__ == '__main__':
    # Test embeddings
    print("🧪 Testing Embeddings Engine", file=sys.stderr)
    print("=" * 50, file=sys.stderr)

    # Check backends
    info = get_backend_info()
    print(f"OpenAI: {'✅' if info['openai'] else '❌'}", file=sys.stderr)
    print(f"Local: {'✅' if info['local'] else '❌'}", file=sys.stderr)
    print(f"Fallback: ✅", file=sys.stderr)
    print(file=sys.stderr)

    # Test similarity
    text1 = "Use TypedDict for configuration objects"
    text2 = "Define configs with TypedDict for type safety"
    text3 = "Use dataclasses for data models"

    print(f"Text 1: {text1}", file=sys.stderr)
    print(f"Text 2: {text2}", file=sys.stderr)
    print(f"Text 3: {text3}", file=sys.stderr)
    print(file=sys.stderr)

    sim12 = calculate_semantic_similarity(text1, text2)
    sim13 = calculate_semantic_similarity(text1, text3)

    print(f"Similarity(1, 2): {sim12:.3f} {'✅ Similar' if sim12 > 0.85 else '❌ Different'}", file=sys.stderr)
    print(f"Similarity(1, 3): {sim13:.3f} {'✅ Similar' if sim13 > 0.85 else '❌ Different'}", file=sys.stderr)

    print(file=sys.stderr)
    print("✅ Embeddings engine ready!", file=sys.stderr)
