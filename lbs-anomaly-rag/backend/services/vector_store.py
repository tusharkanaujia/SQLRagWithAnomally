"""Vector Store Service for Semantic Search over Queries

Uses SentenceTransformer embeddings with numpy-based cosine similarity search.
Persists data to a JSON file for durability.
"""
import numpy as np
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any, Optional
import os
import json
from datetime import datetime


class VectorStore:
    """Manages embeddings and semantic search for queries"""

    def __init__(self, persist_directory: str = None):
        """
        Initialize vector store with local persistence

        Args:
            persist_directory: Directory to persist embeddings (default: ./chroma_db)
        """
        if persist_directory is None:
            base_dir = os.path.dirname(os.path.dirname(__file__))
            persist_directory = os.path.join(base_dir, "chroma_db")

        os.makedirs(persist_directory, exist_ok=True)
        self.persist_path = os.path.join(persist_directory, "vector_store.json")

        # Initialize embedding model (all-MiniLM-L6-v2 - fast and efficient)
        print("Loading embedding model...")
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        print("Embedding model loaded successfully")

        # Load persisted data or start fresh
        self.documents: List[Dict[str, Any]] = []
        self.embeddings: List[List[float]] = []
        self._load()

    def _load(self):
        """Load persisted data from disk"""
        if os.path.exists(self.persist_path):
            try:
                with open(self.persist_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.documents = data.get("documents", [])
                self.embeddings = data.get("embeddings", [])
                print(f"[OK] Loaded {len(self.documents)} examples from vector store")
            except Exception as e:
                print(f"[WARN] Could not load vector store: {e}")
                self.documents = []
                self.embeddings = []

    def _save(self):
        """Persist data to disk"""
        data = {
            "documents": self.documents,
            "embeddings": self.embeddings
        }
        with open(self.persist_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False)

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
        doc_id = f"query_{len(self.documents)}_{datetime.now().timestamp()}"

        # Generate embedding
        embedding = self.embedding_model.encode(question).tolist()

        # Build document
        doc = {
            "id": doc_id,
            "question": question,
            "sql": sql,
            "intent": intent,
            "added_at": datetime.now().isoformat()
        }
        if metadata:
            doc["metadata"] = metadata

        self.documents.append(doc)
        self.embeddings.append(embedding)
        self._save()

        return doc_id

    def search_similar_queries(
        self,
        question: str,
        n_results: int = 5,
        intent_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Find similar queries using cosine similarity

        Args:
            question: Natural language question to search for
            n_results: Number of results to return
            intent_filter: Optional intent to filter by

        Returns:
            List of similar query examples with metadata
        """
        if not self.documents:
            return []

        # Generate query embedding
        query_embedding = self.embedding_model.encode(question)

        # Filter by intent if specified
        indices = list(range(len(self.documents)))
        if intent_filter:
            indices = [i for i in indices if self.documents[i].get("intent") == intent_filter]

        if not indices:
            return []

        # Compute cosine similarities
        doc_embeddings = np.array([self.embeddings[i] for i in indices])
        query_norm = query_embedding / np.linalg.norm(query_embedding)
        doc_norms = doc_embeddings / np.linalg.norm(doc_embeddings, axis=1, keepdims=True)
        similarities = doc_norms @ query_norm

        # Get top-n results
        top_k = min(n_results, len(indices))
        top_indices = np.argsort(similarities)[::-1][:top_k]

        results = []
        for idx in top_indices:
            orig_idx = indices[idx]
            doc = self.documents[orig_idx]
            results.append({
                "id": doc["id"],
                "question": doc["question"],
                "sql": doc["sql"],
                "intent": doc.get("intent", ""),
                "distance": float(1 - similarities[idx]),  # Convert similarity to distance
                "metadata": {k: v for k, v in doc.items() if k not in ("id", "question")}
            })

        return results

    def get_all_examples(self) -> List[Dict[str, Any]]:
        """Get all query examples from the store"""
        return [
            {
                "id": doc["id"],
                "question": doc["question"],
                "sql": doc["sql"],
                "intent": doc.get("intent", ""),
                "metadata": {k: v for k, v in doc.items() if k not in ("id", "question")}
            }
            for doc in self.documents
        ]

    def delete_example(self, doc_id: str) -> bool:
        """Delete a query example by ID"""
        for i, doc in enumerate(self.documents):
            if doc["id"] == doc_id:
                self.documents.pop(i)
                self.embeddings.pop(i)
                self._save()
                return True
        return False

    def clear_all(self) -> bool:
        """Clear all examples from the store"""
        self.documents = []
        self.embeddings = []
        self._save()
        return True

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector store"""
        intents: Dict[str, int] = {}
        for doc in self.documents:
            intent = doc.get("intent", "unknown")
            intents[intent] = intents.get(intent, 0) + 1

        return {
            "total_examples": len(self.documents),
            "intents": intents,
            "embedding_model": "all-MiniLM-L6-v2",
            "embedding_dimension": 384
        }

    def bulk_add_examples(self, examples: List[Dict[str, Any]]) -> int:
        """Add multiple query examples at once"""
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
