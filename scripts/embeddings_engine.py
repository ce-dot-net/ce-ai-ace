#!/usr/bin/env python3
"""
Semantic Similarity Engine with ChromaDB MCP Caching

Uses sentence-transformers with ChromaDB MCP for persistent embedding storage.
Based on ACE paper requirement: "semantic embeddings with 0.85 similarity threshold"

Architecture:
1. Encode pattern text → 384-dim vector (sentence-transformers)
2. Store in ChromaDB MCP collection (persistent cache)
3. Compare via cosine similarity (fast lookups)

Why ChromaDB MCP:
- Persistent storage across sessions (research paper: "semantic embeddings")
- Automatic deduplication (don't recompute same embeddings)
- Fast similarity queries (vector database optimized)
- Plugin-managed (no user setup required)
"""

import json
import hashlib
import sys
from pathlib import Path
from typing import Tuple, Optional, List
import numpy as np

# Lazy imports
_model = None
_chromadb_collection = None

# ChromaDB MCP collection name
COLLECTION_NAME = "ace-pattern-embeddings"
PROJECT_ROOT = Path.cwd()
CHROMADB_PATH = PROJECT_ROOT / '.ace-memory' / 'chromadb'


def get_model():
    """Lazy load sentence-transformers model."""
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
            # Use all-MiniLM-L6-v2: same as ChromaDB default
            # 384-dimensional embeddings, optimized for semantic similarity
            _model = SentenceTransformer('all-MiniLM-L6-v2')
            print("✅ Loaded sentence-transformers model: all-MiniLM-L6-v2", file=sys.stderr)
        except ImportError:
            print("❌ sentence-transformers not installed. Install with: pip install sentence-transformers", file=sys.stderr)
            raise
    return _model


def get_chromadb_collection():
    """
    Get or create ChromaDB collection for embeddings.

    Uses ChromaDB MCP (configured in plugin.json) for persistent storage.
    """
    global _chromadb_collection

    if _chromadb_collection is not None:
        return _chromadb_collection

    try:
        import chromadb
        from chromadb.config import Settings

        # Initialize ChromaDB client pointing to plugin's database
        CHROMADB_PATH.parent.mkdir(parents=True, exist_ok=True)

        client = chromadb.PersistentClient(
            path=str(CHROMADB_PATH),
            settings=Settings(anonymized_telemetry=False)
        )

        # Get or create collection for ACE pattern embeddings
        # Uses default embedding function (same as sentence-transformers)
        _chromadb_collection = client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"description": "ACE pattern embeddings for semantic similarity"}
        )

        print(f"✅ ChromaDB collection ready: {COLLECTION_NAME} ({_chromadb_collection.count()} embeddings cached)", file=sys.stderr)
        return _chromadb_collection

    except ImportError:
        print("⚠️  chromadb not installed, using direct encoding (no caching)", file=sys.stderr)
        return None
    except Exception as e:
        print(f"⚠️  ChromaDB init failed: {e}, using direct encoding", file=sys.stderr)
        return None


def text_to_id(text: str) -> str:
    """Generate stable ID for text (for ChromaDB document ID)."""
    return hashlib.md5(text.encode()).hexdigest()


def get_embedding(text: str, use_cache: bool = True) -> np.ndarray:
    """
    Get embedding for text, using ChromaDB cache if available.

    Args:
        text: Text to embed
        use_cache: Whether to use ChromaDB cache (default: True)

    Returns:
        384-dimensional numpy array
    """
    text_id = text_to_id(text)

    # Try to get from ChromaDB cache
    if use_cache:
        collection = get_chromadb_collection()
        if collection is not None:
            try:
                # Query by ID to get cached embedding
                results = collection.get(ids=[text_id], include=["embeddings"])
                if results and 'embeddings' in results and len(results['embeddings']) > 0:
                    embedding_data = results['embeddings'][0]
                    # Check if embedding data is valid (not empty)
                    if embedding_data is not None and len(embedding_data) > 0:
                        # Cache hit!
                        return np.array(embedding_data)
            except Exception as e:
                print(f"⚠️  ChromaDB cache lookup failed: {e}", file=sys.stderr)

    # Cache miss or cache disabled - compute embedding
    model = get_model()
    embedding = model.encode(text)

    # Store in ChromaDB for future use
    if use_cache:
        collection = get_chromadb_collection()
        if collection is not None:
            try:
                collection.upsert(
                    ids=[text_id],
                    documents=[text],
                    embeddings=[embedding.tolist()]
                )
            except Exception as e:
                print(f"⚠️  ChromaDB cache write failed: {e}", file=sys.stderr)

    return embedding


def calculate_similarity(text1: str, text2: str, use_cache: bool = True) -> Tuple[float, str]:
    """
    Calculate semantic similarity between two texts.

    Uses ChromaDB MCP for caching embeddings to avoid recomputation.

    Args:
        text1: First text (pattern description)
        text2: Second text (pattern description)
        use_cache: Whether to use ChromaDB cache (default: True)

    Returns:
        (similarity_score, method_used)
        - similarity_score: 0.0 to 1.0 (cosine similarity)
        - method_used: 'sentence-transformers' or 'sentence-transformers-cached'

    Examples:
        >>> calculate_similarity("Use TypedDict for configs", "TypedDict for configuration")
        (0.94, 'sentence-transformers-cached')
    """
    # Get embeddings (from cache or compute)
    embedding1 = get_embedding(text1, use_cache=use_cache)
    embedding2 = get_embedding(text2, use_cache=use_cache)

    # Calculate cosine similarity
    from sklearn.metrics.pairwise import cosine_similarity
    similarity = cosine_similarity([embedding1], [embedding2])[0][0]

    method = 'sentence-transformers-cached' if use_cache else 'sentence-transformers'
    return (float(similarity), method)


class SemanticSimilarityEngine:
    """
    Semantic similarity engine with ChromaDB caching.

    Backward compatible with ace-cycle.py.
    """

    def __init__(self, project_root=None, use_cache=True):
        """
        Initialize engine.

        Args:
            project_root: Project root directory (for .ace-memory/)
            use_cache: Whether to use ChromaDB cache (default: True)
        """
        self.use_cache = use_cache
        if project_root:
            global PROJECT_ROOT, CHROMADB_PATH
            PROJECT_ROOT = Path(project_root)
            CHROMADB_PATH = PROJECT_ROOT / '.ace-memory' / 'chromadb'

    def calculate_similarity(self, text1: str, text2: str) -> Tuple[float, str, str]:
        """
        Calculate semantic similarity (backward compatible signature).

        Returns:
            (similarity_score, method_used, reasoning)
        """
        score, method = calculate_similarity(text1, text2, use_cache=self.use_cache)
        reasoning = f"Cosine similarity using {method}: {score:.3f}"
        return (score, method, reasoning)

    def get_cache_stats(self) -> dict:
        """Get ChromaDB cache statistics."""
        collection = get_chromadb_collection()
        if collection is None:
            return {"cached": 0, "status": "unavailable"}

        try:
            count = collection.count()
            return {
                "cached": count,
                "status": "active",
                "collection": COLLECTION_NAME,
                "path": str(CHROMADB_PATH)
            }
        except Exception as e:
            return {"cached": 0, "status": f"error: {e}"}


def test_similarity_engine():
    """Test the similarity engine with sample patterns."""
    test_pairs = [
        ("Use TypedDict for configs", "TypedDict for configuration objects"),
        ("Stripe in services/stripe.ts", "Payments with Stripe SDK"),
        ("Use async/await", "Use TypedDict for configs"),
        ("Use list comprehensions", "Python list comprehensions for iteration"),
    ]

    print("🧪 Testing Semantic Similarity Engine with ChromaDB Caching\n")

    engine = SemanticSimilarityEngine()

    # First pass - compute and cache
    print("=== First Pass (Computing & Caching) ===\n")
    for text1, text2 in test_pairs:
        score, method, reasoning = engine.calculate_similarity(text1, text2)
        print(f"Pattern 1: {text1}")
        print(f"Pattern 2: {text2}")
        print(f"Similarity: {score:.2f} (method: {method})")
        print("-" * 60)

    # Second pass - should use cache
    print("\n=== Second Pass (Using Cache) ===\n")
    for text1, text2 in test_pairs[:2]:  # Just test first 2
        score, method, reasoning = engine.calculate_similarity(text1, text2)
        print(f"Pattern 1: {text1}")
        print(f"Pattern 2: {text2}")
        print(f"Similarity: {score:.2f} (method: {method})")
        print("-" * 60)

    # Show cache stats
    print("\n=== Cache Statistics ===")
    stats = engine.get_cache_stats()
    print(json.dumps(stats, indent=2))


if __name__ == '__main__':
    test_similarity_engine()
