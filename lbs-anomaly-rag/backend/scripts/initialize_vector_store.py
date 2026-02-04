"""Initialize vector store with example queries"""
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from services.vector_store import get_vector_store
from services.schema_context import get_example_queries


def initialize_vector_store():
    """Initialize vector store with example queries from schema_context"""
    print("Initializing vector store...")

    # Get vector store instance
    vector_store = get_vector_store()

    # Get example queries
    examples = get_example_queries()

    print(f"\nFound {len(examples)} example queries")

    # Clear existing examples (optional - comment out to preserve existing)
    print("\nClearing existing examples...")
    vector_store.clear_all()

    # Add examples to vector store
    print("\nAdding examples to vector store...")
    count = vector_store.bulk_add_examples(examples)

    print(f"\n✓ Successfully added {count} examples to vector store")

    # Show stats
    stats = vector_store.get_stats()
    print(f"\nVector Store Stats:")
    print(f"  Total examples: {stats['total_examples']}")
    print(f"  Embedding model: {stats['embedding_model']}")
    print(f"  Embedding dimension: {stats['embedding_dimension']}")
    print(f"\n  Examples by intent:")
    for intent, count in stats['intents'].items():
        print(f"    - {intent}: {count}")

    # Test semantic search
    print("\n" + "="*60)
    print("Testing semantic search:")
    print("="*60)

    test_questions = [
        "What are the highest revenue customers?",
        "Show me sales trends by month",
        "Which products generate the most income?"
    ]

    for test_q in test_questions:
        print(f"\nQuery: '{test_q}'")
        results = vector_store.search_similar_queries(test_q, n_results=2)
        print(f"Top 2 similar examples:")
        for i, result in enumerate(results, 1):
            print(f"  {i}. [{result['intent']}] {result['question']}")
            print(f"     Distance: {result['distance']:.4f}")

    print("\n✓ Vector store initialized successfully!")


if __name__ == "__main__":
    initialize_vector_store()
