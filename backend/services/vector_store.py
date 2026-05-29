"""
Vextral Vector Store Service
Manages all interactions with vector database (Qdrant Cloud or Serverless LanceDB)
Implements multi-tenancy with per-user collections/tables for data isolation
"""

import os
import pyarrow as pa
from dotenv import load_dotenv
from uuid import uuid4

load_dotenv()

# Check which vector store to use
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_KEY = os.getenv("QDRANT_KEY")
IS_LANCE = not bool(QDRANT_URL and QDRANT_KEY)

if IS_LANCE:
    import lancedb
    LANCE_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "vextral_lancedb")
    # Ensure directory exists
    os.makedirs(os.path.dirname(LANCE_DB_PATH), exist_ok=True)
    os.makedirs(LANCE_DB_PATH, exist_ok=True)
    lancedb_client = lancedb.connect(LANCE_DB_PATH)
else:
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
    lancedb_client = None


class VectorStoreService:
    """Service for managing vector storage (LanceDB or Qdrant Cloud)"""
    
    def __init__(self):
        """Initialize Qdrant or LanceDB client"""
        self.vector_size = 2048  # Llama-Nemotron embedding dimension
        
        if not IS_LANCE:
            self.client = QdrantClient(
                url=QDRANT_URL,
                api_key=QDRANT_KEY,
                timeout=60
            )
            print("[OK] Initialized Qdrant Cloud Vector Store")
        else:
            self.db = lancedb_client
            print(f"[OK] Initialized Serverless LanceDB Vector Store at: {LANCE_DB_PATH}")
    
    def ensure_collection(self, tenant_id: str):
        """
        Create a Qdrant collection or LanceDB table for this tenant if it doesn't exist
        """
        collection_name = f"tenant_{tenant_id}"
        
        if IS_LANCE:
            try:
                if collection_name not in self.db.table_names():
                    # Define Arrow schema for LanceDB
                    schema = pa.schema([
                        pa.field("id", pa.string()),
                        pa.field("vector", pa.list_(pa.float32(), self.vector_size)),
                        pa.field("text", pa.string()),
                        pa.field("parent_text", pa.string(), nullable=True),
                        pa.field("parent_id", pa.string(), nullable=True),
                        pa.field("source_file", pa.string()),
                        pa.field("page_number", pa.int32(), nullable=True),
                        pa.field("chunk_type", pa.string(), nullable=True),
                        pa.field("chunk_index", pa.int32(), nullable=True),
                    ])
                    self.db.create_table(collection_name, schema=schema)
                    print(f"[OK] Created LanceDB table: {collection_name}")
            except Exception as e:
                print(f"Error ensuring LanceDB table for {tenant_id}: {e}")
        else:
            try:
                # Check if collection exists
                collections = self.client.get_collections().collections
                collection_names = [c.name for c in collections]
                
                if collection_name not in collection_names:
                    # Create new collection
                    self.client.create_collection(
                        collection_name=collection_name,
                        vectors_config=VectorParams(
                            size=self.vector_size,
                            distance=Distance.COSINE
                        )
                    )
                    print(f"[OK] Created Qdrant collection: {collection_name}")
                
                # Ensure index on source_file exists
                self.client.create_payload_index(
                    collection_name=collection_name,
                    field_name="source_file",
                    field_schema="keyword"
                )
                    
            except Exception as e:
                if "already exists" not in str(e).lower():
                    print(f"Error ensuring Qdrant collection/index for {tenant_id}: {e}")
    
    def upsert_chunks(self, tenant_id: str, chunks: list[dict]):
        """
        Save document chunks to the tenant's vector table
        """
        self.ensure_collection(tenant_id)
        collection_name = f"tenant_{tenant_id}"
        
        if IS_LANCE:
            try:
                table = self.db.open_table(collection_name)
                data_rows = []
                for chunk in chunks:
                    data_rows.append({
                        "id": chunk.get("id", str(uuid4())),
                        "vector": chunk["vector"],
                        "text": chunk["text"],
                        "parent_text": chunk.get("parent_text"),
                        "parent_id": chunk.get("parent_id"),
                        "source_file": chunk["source_file"],
                        "page_number": chunk.get("page_number", 0),
                        "chunk_type": chunk.get("chunk_type", "text"),
                        "chunk_index": chunk.get("chunk_index", 0)
                    })
                
                # LanceDB does very efficient batching natively
                table.add(data_rows)
                print(f"[OK] Upserted {len(data_rows)} chunks to LanceDB table {collection_name}")
            except Exception as e:
                print(f"Error upserting chunks in LanceDB for {tenant_id}: {e}")
                raise Exception(f"Failed to upsert chunks: {str(e)}")
        else:
            try:
                points = []
                for chunk in chunks:
                    point = PointStruct(
                        id=chunk.get("id", str(uuid4())),
                        vector=chunk["vector"],
                        payload={
                            "text": chunk["text"],
                            "parent_text": chunk.get("parent_text"),
                            "parent_id": chunk.get("parent_id"),
                            "source_file": chunk["source_file"],
                            "page_number": chunk.get("page_number", 0),
                            "chunk_type": chunk.get("chunk_type", "text"),
                            "chunk_index": chunk.get("chunk_index", 0)
                        }
                    )
                    points.append(point)
                
                batch_size = 150
                total_batches = (len(points) + batch_size - 1) // batch_size
                
                for i in range(0, len(points), batch_size):
                    batch = points[i:i + batch_size]
                    batch_num = (i // batch_size) + 1
                    
                    self.client.upsert(
                        collection_name=collection_name,
                        points=batch
                    )
                    print(f"  [OK] Uploaded batch {batch_num}/{total_batches} ({len(batch)} chunks)")
                
                print(f"[OK] Upserted {len(points)} chunks to Qdrant collection {collection_name}")
                
            except Exception as e:
                print(f"Error upserting chunks in Qdrant for {tenant_id}: {e}")
                raise Exception(f"Failed to upsert chunks: {str(e)}")
    
    def search_chunks_detailed(
        self,
        tenant_id: str,
        query_vector: list[float],
        top_k: int = 5,
        source_file: str = None
    ) -> list[dict]:
        """
        Search for the most similar chunks in the tenant's vector database
        """
        collection_name = f"tenant_{tenant_id}"
        
        if IS_LANCE:
            try:
                if collection_name not in self.db.table_names():
                    print(f"  ⚠️ Table {collection_name} does not exist yet")
                    return []
                
                table = self.db.open_table(collection_name)
                
                # Build vector search query
                query = table.search(query_vector).metric("cosine").limit(top_k)
                
                if source_file:
                    query = query.where(f"source_file = '{source_file}'")
                    print(f"  🔍 Filtering LanceDB search to: {source_file}")
                
                results = query.to_list()
                
                chunks: list[dict] = []
                for result in results:
                    text = str(result.get("text", "")).strip()
                    if not text:
                        continue
                    
                    # Convert distance to cosine similarity score (cosine distance is 1.0 - similarity)
                    # So similarity score = 1.0 - distance
                    distance = result.get("_distance", 0.0)
                    score = float(1.0 - distance)
                    
                    chunks.append({
                        "text": text,
                        "parent_text": result.get("parent_text"),
                        "parent_id": result.get("parent_id"),
                        "score": score,
                        "source_file": result.get("source_file", source_file),
                        "page_number": result.get("page_number", 0),
                        "chunk_type": result.get("chunk_type", "text"),
                        "chunk_index": result.get("chunk_index", 0),
                    })
                
                # Debug print
                if chunks:
                    for i, r in enumerate(chunks[:3]):
                        preview = str(r.get("text", ""))[:60]
                        print(f"  Result {i+1}: score={r['score']:.4f}, text={preview}...")
                else:
                    print(f"  ⚠️ No results found")
                
                print(f"[OK] Found {len(chunks)} relevant chunks from LanceDB")
                return chunks
                
            except Exception as e:
                print(f"Error searching chunks in LanceDB for {tenant_id}: {e}")
                return []
        else:
            try:
                # Build filter for document-specific search
                query_filter = None
                if source_file:
                    query_filter = Filter(
                        must=[
                            FieldCondition(
                                key="source_file",
                                match=MatchValue(value=source_file)
                            )
                        ]
                    )
                    print(f"  🔍 Filtering search to: {source_file}")
                
                # Search with optional filter
                results = self.client.search(
                    collection_name=collection_name,
                    query_vector=query_vector,
                    query_filter=query_filter,
                    limit=top_k
                )
                
                # Debug: print scores
                if results:
                    for i, r in enumerate(results[:3]):
                        payload = r.payload or {}
                        preview = str(payload.get("text", ""))[:60]
                        print(f"  Result {i+1}: score={r.score:.4f}, text={preview}...")
                else:
                    print(f"  ⚠️ No results found")
                
                chunks: list[dict] = []
                for result in results:
                    payload = result.payload or {}
                    text = str(payload.get("text", "")).strip()
                    if not text:
                        continue

                    chunks.append({
                        "text": text,
                        "parent_text": payload.get("parent_text"),
                        "parent_id": payload.get("parent_id"),
                        "score": float(result.score) if result.score is not None else 0.0,
                        "source_file": payload.get("source_file", source_file),
                        "page_number": payload.get("page_number", 0),
                        "chunk_type": payload.get("chunk_type", "text"),
                        "chunk_index": payload.get("chunk_index", 0),
                    })

                print(f"[OK] Found {len(chunks)} relevant chunks")
                return chunks
                
            except Exception as e:
                print(f"Error searching chunks for {tenant_id}: {e}")
                return []

    def search_chunks(self, tenant_id: str, query_vector: list[float], top_k: int = 5, source_file: str = None) -> list[str]:
        """
        Backward-compatible wrapper that returns only chunk texts.
        """
        detailed_chunks = self.search_chunks_detailed(
            tenant_id=tenant_id,
            query_vector=query_vector,
            top_k=top_k,
            source_file=source_file
        )
        return [chunk["text"] for chunk in detailed_chunks]
    
    def delete_document(self, tenant_id: str, source_file: str):
        """
        Delete all chunks from a specific document
        """
        self.ensure_collection(tenant_id)
        collection_name = f"tenant_{tenant_id}"
        
        if IS_LANCE:
            try:
                table = self.db.open_table(collection_name)
                # Escape single quotes in source_file to avoid SQL syntax errors
                safe_file = source_file.replace("'", "''")
                table.delete(f"source_file = '{safe_file}'")
                print(f"[OK] Deleted all chunks from {source_file} in LanceDB")
            except Exception as e:
                print(f"Error deleting document in LanceDB for {tenant_id}: {e}")
                raise Exception(f"Failed to delete document: {str(e)}")
        else:
            try:
                self.client.delete(
                    collection_name=collection_name,
                    points_selector=Filter(
                        must=[
                            FieldCondition(
                                key="source_file",
                                match=MatchValue(value=source_file)
                            )
                        ]
                    )
                )
                print(f"[OK] Deleted all chunks from {source_file} in Qdrant")
                
            except Exception as e:
                print(f"Error deleting document {source_file} for {tenant_id}: {e}")
                raise Exception(f"Failed to delete document: {str(e)}")


# Singleton instance
vector_store = VectorStoreService()


if __name__ == "__main__":
    print("Testing Vextral Vector Store Service...")
    test_tenant = "test_user"
    
    try:
        vector_store.ensure_collection(test_tenant)
        test_chunks = [
            {
                "id": "test1",
                "vector": [0.1] * 2048,
                "text": "This is a test chunk about Vextral.",
                "source_file": "test.pdf",
                "page_number": 1
            },
            {
                "id": "test2",
                "vector": [0.2] * 2048,
                "text": "Another test chunk about document processing.",
                "source_file": "test.pdf",
                "page_number": 2
            }
        ]
        vector_store.upsert_chunks(test_tenant, test_chunks)
        query_vector = [0.15] * 2048
        results = vector_store.search_chunks(test_tenant, query_vector, top_k=2)
        print(f"[OK] Search results: {len(results)} chunks found")
        print("\n[OK] ALL VECTOR STORE TESTS PASSED")
    except Exception as e:
        print(f"✗ Test failed: {e}")

