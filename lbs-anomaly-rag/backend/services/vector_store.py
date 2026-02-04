"""Vector Store Service for Semantic Search over Queries"""
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any, Optional
import os
import json
from datetime import datetime


class VectorStore:
    """Manages embeddings and semantic search for queries"""

    def __init__(self, persist_directory: str = None):
        """
        Initialize vector store with ChromaDB

        Args:
            persist_directory: Directory to persist embeddings (default: ./chroma_db)
        """
        if persist_directory is None:
            # Store in backend directory
            base_dir = os.path.dirname(os.path.dirname(__file__))
            persist_directory = os.path.join(base_dir, "chroma_db")

        # Initialize ChromaDB client
        self.client = chromadb.Client(Settings(
            persist_directory=persist_directory,
            anonymized_telemetry=False
        ))

        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name="query_examples",
            metadata={"description": "SQL query examples for semantic search"}
        )

        # Initialize embedding model (using all-MiniLM-L6-v2 - fast and efficient)
        print("Loading embedding model...")
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        print("Embedding model loaded successfully")

    def add_query_example(
        self,
        question: str,
        sql: str,
        intent: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Add a query example to the vector store

        Args:
            question: Natural language question
            sql: SQL query
            intent: Query intent/category
            metadata: Additional metadata

        Returns:
            Document ID
        """
        # Generate unique ID
        doc_id = f"query_{len(self.collection.get()['ids'])}_{ datetime.now().timestamp()}"

        # Generate embedding for the question
        embedding = self.embedding_model.encode(question).tolist()

        # Prepare metadata
        doc_metadata = {
            "intent": intent,
            "sql": sql,
            "added_at": datetime.now().isoformat()
        }
        if metadata:
            doc_metadata.update(metadata)

        # Add to collection
        self.collection.add(
            ids=[doc_id],
            embeddings=[embedding],
            documents=[question],
            metadatas=[doc_metadata]
        )

        return doc_id

    def search_similar_queries(
        self,
        question: str,
        n_results: int = 5,
        intent_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Find similar queries using semantic search

        Args:
            question: Natural language question to search for
            n_results: Number of results to return
            intent_filter: Optional intent to filter by

        Returns:
            List of similar query examples with metadata
        """
        # Generate embedding for search query
        query_embedding = self.embedding_model.encode(question).tolist()

        # Build where filter if intent specified
        where_filter = None
        if intent_filter:
            where_filter = {"intent": intent_filter}

        # Search for similar queries
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where_filter
        )

        # Format results
        similar_queries = []
        if results and results['ids']:
            for i in range(len(results['ids'][0])):
                similar_queries.append({
                    "id": results['ids'][0][i],
                    "question": results['documents'][0][i],
                    "sql": results['metadatas'][0][i].get('sql', ''),
                    "intent": results['metadatas'][0][i].get('intent', ''),
                    "distance": results['distances'][0][i] if 'distances' in results else None,
                    "metadata": results['metadatas'][0][i]
                })

        return similar_queries

    def get_all_examples(self) -> List[Dict[str, Any]]:
        """
        Get all query examples from the store

        Returns:
            List of all query examples
        """
        results = self.collection.get()

        examples = []
        if results and results['ids']:
            for i in range(len(results['ids'])):
                examples.append({
                    "id": results['ids'][i],
                    "question": results['documents'][i],
                    "sql": results['metadatas'][i].get('sql', ''),
                    "intent": results['metadatas'][i].get('intent', ''),
                    "metadata": results['metadatas'][i]
                })

        return examples

    def delete_example(self, doc_id: str) -> bool:
        """
        Delete a query example

        Args:
            doc_id: Document ID to delete

        Returns:
            True if deleted successfully
        """
        try:
            self.collection.delete(ids=[doc_id])
            return True
        except Exception:
            return False

    def clear_all(self) -> bool:
        """
        Clear all examples from the store

        Returns:
            True if cleared successfully
        """
        try:
            # Delete the collection and recreate it
            self.client.delete_collection("query_examples")
            self.collection = self.client.get_or_create_collection(
                name="query_examples",
                metadata={"description": "SQL query examples for semantic search"}
            )
            return True
        except Exception:
            return False

    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the vector store

        Returns:
            Dictionary with stats
        """
        all_examples = self.collection.get()

        intents = {}
        if all_examples and all_examples['metadatas']:
            for metadata in all_examples['metadatas']:
                intent = metadata.get('intent', 'unknown')
                intents[intent] = intents.get(intent, 0) + 1

        return {
            "total_examples": len(all_examples['ids']) if all_examples else 0,
            "intents": intents,
            "embedding_model": "all-MiniLM-L6-v2",
            "embedding_dimension": 384
        }

    def bulk_add_examples(self, examples: List[Dict[str, Any]]) -> int:
        """
        Add multiple query examples at once

        Args:
            examples: List of dicts with 'question', 'sql', 'intent' keys

        Returns:
            Number of examples added
        """
        count = 0
        for example in examples:
            try:
                self.add_query_example(
                    question=example['question'],
                    sql=example['sql'],
                    intent=example.get('intent', 'general_query'),
                    metadata=example.get('metadata')
                )
                count += 1
            except Exception as e:
                print(f"Error adding example: {e}")
                continue

        return count


# Global instance
_vector_store = None


def get_vector_store() -> VectorStore:
    """Get singleton vector store instance"""
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore()
    return _vector_store
