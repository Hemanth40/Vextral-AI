"""
Vextral Backend Service Tests
Tests all core services before deployment
"""

import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.embedder import embedder
from services.generator import generator
from services.parser import parser


def test_embedder():
    """Test the embedding service"""
    print("\n" + "="*60)
    print("TEST 1: Embedder Service")
    print("="*60)
    
    try:
        # Test text embedding
        test_text = "Vextral is a multi-tenant RAG platform"
        embedding = embedder.embed_text(test_text)
        
        assert len(embedding) == 2048, f"Expected 2048 dimensions, got {len(embedding)}"
        assert all(isinstance(x, float) for x in embedding), "All values should be floats"
        
        print(f"✓ Text embedding successful")
        print(f"  Vector length: {len(embedding)}")
        print(f"  First 5 values: {embedding[:5]}")
        print(f"  Sample range: [{min(embedding):.4f}, {max(embedding):.4f}]")
        return True
        
    except Exception as e:
        print(f"✗ Embedder test failed: {e}")
        return False


def test_parser():
    """Test the document parser"""
    print("\n" + "="*60)
    print("TEST 2: Parser Service")
    print("="*60)
    
    try:
        # Test text chunking
        long_text = "This is a test sentence. " * 100
        chunks = parser.chunk_text(long_text, max_words=50)
        
        assert len(chunks) > 0, "Should create at least one chunk"
        assert all(isinstance(chunk, str) for chunk in chunks), "All chunks should be strings"
        
        print(f"✓ Text chunking successful")
        print(f"  Created {len(chunks)} chunks from long text")
        print(f"  Average chunk length: {sum(len(c.split()) for c in chunks) / len(chunks):.1f} words")
        return True
        
    except Exception as e:
        print(f"✗ Parser test failed: {e}")
        return False


def test_generator():
    """Test the answer generation service"""
    print("\n" + "="*60)
    print("TEST 3: Generator Service")
    print("="*60)
    
    try:
        # Test answer generation
        question = "What is Vextral?"
        context = [
            "Vextral is a multi-tenant SaaS platform for document intelligence.",
            "It uses NVIDIA NIM models for embedding and answer generation."
        ]
        
        answer = generator.generate_answer(question, context, "test_user")
        
        assert isinstance(answer, str), "Answer should be a string"
        assert len(answer) > 10, "Answer should be meaningful"
        
        print(f"✓ Answer generation successful")
        print(f"  Question: {question}")
        print(f"  Answer length: {len(answer)} characters")
        print(f"  Answer preview: {answer[:100]}...")
        return True
        
    except Exception as e:
        print(f"✗ Generator test failed: {e}")
        return False


def main():
    """Run all tests"""
    print("\n" + "🧪 "*20)
    print("VEXTRAL BACKEND SERVICE TESTS")
    print("🧪 "*20)
    
    results = []
    
    # Run tests
    results.append(("Embedder", test_embedder()))
    results.append(("Parser", test_parser()))
    results.append(("Generator", test_generator()))
    
    # Print summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    for name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{name:20} {status}")
    
    all_passed = all(result[1] for result in results)
    
    if all_passed:
        print("\n" + "🎉 "*20)
        print("ALL TESTS PASSED ✓")
        print("🎉 "*20 + "\n")
        return 0
    else:
        print("\n" + "❌ "*20)
        print("SOME TESTS FAILED")
        print("❌ "*20 + "\n")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
