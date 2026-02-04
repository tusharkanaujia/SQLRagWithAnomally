# Vector Store Guide

## Overview

The vector store adds **semantic search** capabilities to the RAG system. Instead of using hardcoded example queries, the system can now:

- ✅ Find similar queries using AI embeddings
- ✅ Retrieve the most relevant examples for each question
- ✅ Learn from new query patterns you add
- ✅ Improve SQL generation accuracy over time

## How It Works

### Traditional Approach (Old)
```
User Question → Hardcoded Examples → LLM → SQL
```

### Vector Store Approach (New)
```
User Question → Semantic Search → Most Similar Examples → LLM → SQL
                      ↓
                Vector Database
              (ChromaDB + Embeddings)
```

## Installation

1. **Install dependencies:**
```bash
cd backend
pip install chromadb sentence-transformers
```

Or install all requirements:
```bash
pip install -r requirements.txt
```

2. **Initialize the vector store:**
```bash
python scripts/initialize_vector_store.py
```

This will:
- Create a `chroma_db/` directory
- Load the embedding model (all-MiniLM-L6-v2)
- Add all example queries from [schema_context.py](services/schema_context.py)
- Test semantic search

## Storage Location

Embeddings are stored in:
```
backend/
  └── chroma_db/           # Vector database files
      ├── chroma.sqlite3   # Metadata and index
      └── [uuid]/          # Embedding vectors
```

This directory is automatically created and persisted locally.

## Using the Vector Store

### Via API Endpoints

#### 1. Initialize with Example Queries
```bash
POST http://localhost:8000/vector-store/initialize
```

Response:
```json
{
  "success": true,
  "examples_added": 8,
  "stats": {
    "total_examples": 8,
    "embedding_model": "all-MiniLM-L6-v2",
    "embedding_dimension": 384
  }
}
```

#### 2. Search for Similar Queries
```bash
POST http://localhost:8000/vector-store/search
Content-Type: application/json

{
  "question": "Who bought the most products?",
  "n_results": 3
}
```

Response:
```json
{
  "question": "Who bought the most products?",
  "results": [
    {
      "id": "query_0_1234567890",
      "question": "Who are the top 10 customers by total purchases?",
      "sql": "SELECT TOP 10...",
      "intent": "top_customers",
      "distance": 0.12
    }
  ],
  "count": 3
}
```

#### 3. Add New Query Example
```bash
POST http://localhost:8000/vector-store/add
Content-Type: application/json

{
  "question": "What are the slowest selling products?",
  "sql": "SELECT TOP 10 prod.EnglishProductName, SUM(sal.OrderQuantity) AS TotalQty FROM FactInternetSales sal INNER JOIN DimProduct prod ON prod.ProductKey = sal.ProductKey GROUP BY prod.ProductKey, prod.EnglishProductName ORDER BY TotalQty ASC",
  "intent": "product_analysis"
}
```

#### 4. Get Vector Store Statistics
```bash
GET http://localhost:8000/vector-store/stats
```

Response:
```json
{
  "total_examples": 9,
  "intents": {
    "top_customers": 1,
    "aggregate_sales": 1,
    "product_analysis": 2
  },
  "embedding_model": "all-MiniLM-L6-v2",
  "embedding_dimension": 384
}
```

#### 5. Get All Examples
```bash
GET http://localhost:8000/vector-store/examples
```

#### 6. Delete an Example
```bash
DELETE http://localhost:8000/vector-store/example/{doc_id}
```

### Via Python Code

```python
from services.vector_store import get_vector_store

# Get vector store instance
vector_store = get_vector_store()

# Add a query example
vector_store.add_query_example(
    question="What were the total sales in Q1?",
    sql="SELECT SUM(SalesAmount) FROM FactInternetSales WHERE...",
    intent="aggregate_sales"
)

# Search for similar queries
results = vector_store.search_similar_queries(
    question="Show me revenue for first quarter",
    n_results=5
)

for result in results:
    print(f"{result['question']} (distance: {result['distance']:.2f})")

# Get stats
stats = vector_store.get_stats()
print(f"Total examples: {stats['total_examples']}")
```

## How the RAG Service Uses It

The [RAGService](services/rag_service.py) automatically uses vector search when enabled:

```python
# Initialization
rag_service = RAGService(use_vector_search=True)

# When generating SQL
def generate_sql(self, question: str):
    # 1. Use semantic search to find similar queries
    similar_examples = self.vector_store.search_similar_queries(
        question=question,
        n_results=5
    )

    # 2. Use these examples in the prompt
    examples_text = format_examples(similar_examples)

    # 3. Send to LLM with relevant examples
    sql = self._call_llama(prompt_with_examples)
```

**Benefits:**
- More relevant examples for each specific question
- Better SQL generation accuracy
- Adapts to new query patterns you add

## Embedding Model

**Model:** `all-MiniLM-L6-v2`
- **Size:** 80 MB
- **Dimension:** 384
- **Speed:** Fast (~5ms per query)
- **Quality:** Good for semantic search
- **Language:** English
- **Offline:** Works without internet

### Why This Model?

1. **Fast** - Suitable for real-time API responses
2. **Small** - Low memory footprint
3. **Accurate** - Good semantic understanding
4. **Free** - Open source, no API costs
5. **Local** - No external API calls needed

## Advanced Usage

### Filter by Intent

Search only within specific query types:

```python
results = vector_store.search_similar_queries(
    question="Show customer demographics",
    n_results=5,
    intent_filter="customer_analysis"  # Only search customer queries
)
```

### Bulk Add Examples

```python
examples = [
    {
        "question": "Query 1",
        "sql": "SELECT...",
        "intent": "ranking"
    },
    {
        "question": "Query 2",
        "sql": "SELECT...",
        "intent": "aggregation"
    }
]

count = vector_store.bulk_add_examples(examples)
print(f"Added {count} examples")
```

### Clear and Rebuild

```python
# Clear all examples
vector_store.clear_all()

# Reinitialize from schema_context
from services.schema_context import get_example_queries
examples = get_example_queries()
vector_store.bulk_add_examples(examples)
```

## Performance Considerations

### Storage Size

- **Per example:** ~1.5 KB (embedding + metadata)
- **1,000 examples:** ~1.5 MB
- **10,000 examples:** ~15 MB

### Query Speed

- **Semantic search:** 5-20ms for 1,000 examples
- **Embedding generation:** ~5ms per query
- **Total overhead:** ~10-25ms per SQL generation

This is negligible compared to LLM inference time (1-3 seconds).

### Scaling

The current setup (ChromaDB with local persistence) works well for:
- ✅ Up to 10,000 query examples
- ✅ Single server deployment
- ✅ Low-latency semantic search

For larger scale (100k+ examples or distributed deployment):
- Consider Pinecone, Weaviate, or Qdrant
- Update [vector_store.py](services/vector_store.py) with new client

## Troubleshooting

### Error: "No module named 'chromadb'"

Install dependencies:
```bash
pip install chromadb sentence-transformers
```

### Error: "Vector store initialization failed"

The RAG service will automatically fall back to hardcoded examples. Check:
1. ChromaDB is installed
2. Directory permissions for `chroma_db/`
3. Sufficient disk space

### Slow First Query

The first query loads the embedding model (~80MB) into memory. Subsequent queries are fast.

### Want to Use a Different Embedding Model?

Edit [vector_store.py:37](services/vector_store.py#L37):

```python
# Options:
self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')      # Fast, 384 dim
self.embedding_model = SentenceTransformer('all-mpnet-base-v2')    # Better quality, 768 dim
self.embedding_model = SentenceTransformer('multi-qa-mpnet-base')  # Best for Q&A
```

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    User Question                        │
│            "What were sales in 2013?"                   │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│              RAG Service (rag_service.py)               │
├─────────────────────────────────────────────────────────┤
│  1. Generate embedding for question                     │
│  2. Search vector store for similar queries             │
│  3. Retrieve top 5 relevant examples                    │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│          Vector Store (vector_store.py)                 │
├─────────────────────────────────────────────────────────┤
│  • SentenceTransformer (embedding model)                │
│  • ChromaDB (vector database)                           │
│  • Semantic search using cosine similarity              │
└────────────────────┬────────────────────────────────────┘
                     │
                     ├──────────────────────────┐
                     ▼                          ▼
    ┌────────────────────────┐   ┌─────────────────────────┐
    │   Similar Examples     │   │    chroma_db/           │
    ├────────────────────────┤   ├─────────────────────────┤
    │ Q: "Total sales 2013?" │   │  • Embeddings (vectors) │
    │ SQL: SELECT SUM...     │   │  • Metadata             │
    │ Intent: aggregate      │   │  • Index                │
    └────────────┬───────────┘   └─────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│              LLM Prompt Construction                    │
├─────────────────────────────────────────────────────────┤
│  Schema Context + Similar Examples + User Question      │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│           Llama (via Ollama) → SQL Generation           │
└─────────────────────────────────────────────────────────┘
```

## Best Practices

1. **Start with default examples** - Initialize with schema_context examples
2. **Add successful queries** - When a user query generates good SQL, add it to the store
3. **Review periodically** - Check stats to see distribution of intents
4. **Clean up bad examples** - Delete examples that lead to incorrect SQL
5. **Group by intent** - Maintain balanced examples across different query types
6. **Test semantic search** - Use `/vector-store/search` to verify similarity matching

## Next Steps

1. **Initialize:** Run `python scripts/initialize_vector_store.py`
2. **Test:** Use the API endpoints to search and add examples
3. **Monitor:** Check `/vector-store/stats` regularly
4. **Expand:** Add new query patterns as your users ask different questions
5. **Optimize:** Tune n_results (number of examples) based on SQL generation quality

## Related Files

- [vector_store.py](services/vector_store.py) - Vector store implementation
- [rag_service.py](services/rag_service.py) - RAG service using vector search
- [initialize_vector_store.py](scripts/initialize_vector_store.py) - Initialization script
- [main.py](main.py) - API endpoints for vector store management

For questions or issues, check the implementation in the files above.
