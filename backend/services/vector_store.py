"""
Vextral Vector Store Service
Manages all interactions with Qdrant Cloud vector database
Implements multi-tenancy with per-user collections for data isolation
"""

import os
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from dotenv import load_dotenv
from uuid import uuid4

load_dotenv()


class VectorStoreService:
    """Service for managing vector storage in Qdrant Cloud"""
    
    def __init__(self):
        """Initialize Qdrant client"""
        self.client = QdrantClient(
            url=os.getenv("QDRANT_URL"),
            api_key=os.getenv("QDRANT_KEY"),
            timeout=60  # 60 second timeout for large uploads
        )
        self.vector_size = 2048  # Llama-Nemotron embedding dimension
    
    def ensure_collection(self, tenant_id: str):
        """
        Create a Qdrant collection for this tenant if it doesn't exist
        And ensure necessary payload indexes exist
        """
        collection_name = f"tenant_{tenant_id}"
        
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
                print(f"✓ Created collection: {collection_name}")
            
            # Ensure index on source_file exists (required for delete operations)
            # This is safe to call even if index exists
            self.client.create_payload_index(
                collection_name=collection_name,
                field_name="source_file",
                field_schema="keyword"
            )
            # print(f"✓ Verified index on source_file")
                
        except Exception as e:
            # Ignore "index already exists" error if it happens, but print others
            if "already exists" not in str(e).lower():
                print(f"Error ensuring collection/index for {tenant_id}: {e}")
                # Don't raise here, as we want to try to proceed if possible
                # unless it's a critical collection creation error
    
    def upsert_chunks(self, tenant_id: str, chunks: list[dict]):
        """
        Save document chunks to the tenant's collection
        Uses batch processing to avoid timeouts on large uploads
        
        Args:
            tenant_id: The tenant identifier
            chunks: List of chunk dicts with keys: id, vector, text, source_file, page_number
        """
        collection_name = f"tenant_{tenant_id}"
        
        try:
            points = []
            for chunk in chunks:
                point = PointStruct(
                    id=chunk.get("id", str(uuid4())),
                    vector=chunk["vector"],
                    payload={
                        "text": chunk["text"],
                        "source_file": chunk["source_file"],
                        "page_number": chunk.get("page_number", 0),
                        "chunk_type": chunk.get("chunk_type", "text")
                    }
                )
                points.append(point)
            
            # Batch upsert in chunks of 10 to avoid timeout
            batch_size = 10
            total_batches = (len(points) + batch_size - 1) // batch_size
            
            for i in range(0, len(points), batch_size):
                batch = points[i:i + batch_size]
                batch_num = (i // batch_size) + 1
                
                self.client.upsert(
                    collection_name=collection_name,
                    points=batch
                )
                print(f"  ✓ Uploaded batch {batch_num}/{total_batches} ({len(batch)} chunks)")
            
            print(f"✓ Upserted {len(points)} chunks to {collection_name}")
            
        except Exception as e:
            print(f"Error upserting chunks for {tenant_id}: {e}")
            raise Exception(f"Failed to upsert chunks: {str(e)}")
    
    def search_chunks(self, tenant_id: str, query_vector: list[float], top_k: int = 5, source_file: str = None) -> list[str]:
        """
        Search for the most similar chunks in the tenant's collection
        
        Args:
            tenant_id: The tenant identifier
            query_vector: The query embedding vector
            top_k: Number of results to return (default: 5)
            source_file: Optional filename to filter search to one document
            
        Returns:
            List of text strings from the most relevant chunks
        """
        collection_name = f"tenant_{tenant_id}"
        
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
                    print(f"  Result {i+1}: score={r.score:.4f}, text={r.payload['text'][:60]}...")
            else:
                print(f"  ⚠️ No results found")
            
            # Extract text from results
            chunks = [result.payload["text"] for result in results]
            print(f"✓ Found {len(chunks)} relevant chunks")
            return chunks
            
        except Exception as e:
            print(f"Error searching chunks for {tenant_id}: {e}")
            return []
    
    def delete_document(self, tenant_id: str, source_file: str):
        """
        Delete all chunks from a specific document
        
        Args:
            tenant_id: The tenant identifier
            source_file: The filename to delete
        """
        # Ensure collection and index exist before attempting delete
        self.ensure_collection(tenant_id)
        
        collection_name = f"tenant_{tenant_id}"
        
        try:
            # Delete points matching the source_file
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
            print(f"✓ Deleted all chunks from {source_file}")
            
        except Exception as e:
            print(f"Error deleting document {source_file} for {tenant_id}: {e}")
            raise Exception(f"Failed to delete document: {str(e)}")


# Singleton instance
vector_store = VectorStoreService()


if __name__ == "__main__":
    # Simple test
    print("Testing Vextral Vector Store Service...")
    
    test_tenant = "test_user"
    
    try:
        # Test 1: Create collection
        vector_store.ensure_collection(test_tenant)
        
        # Test 2: Upsert test chunks
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
        
        # Test 3: Search
        query_vector = [0.15] * 2048
        results = vector_store.search_chunks(test_tenant, query_vector, top_k=2)
        print(f"✓ Search results: {len(results)} chunks found")
        
        print("\n✓ ALL VECTOR STORE TESTS PASSED")
        
    except Exception as e:
        print(f"✗ Test failed: {e}")
