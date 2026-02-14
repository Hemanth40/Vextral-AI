"""
Vextral Embedding Service
Uses NVIDIA NIM API with Llama-Nemotron-Embed-VL-1B-v2 for multimodal embeddings
Converts text and images into 2048-dimensional vectors
"""

import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


class EmbedderService:
    """Service for generating embeddings using NVIDIA NIM API"""
    
    def __init__(self):
        """Initialize the NVIDIA NIM client"""
        # Use the provided API key for llama-nemotron-embed-vl-1b-v2
        api_key = os.getenv("NVIDIA_API_KEY", "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")
        
        self.client = OpenAI(
            base_url="https://integrate.api.nvidia.com/v1",
            api_key=api_key
        )
        self.model = "nvidia/llama-nemotron-embed-vl-1b-v2"
    
    def embed_text(self, text: str, input_type: str = "passage") -> list[float]:
        """
        Convert text into a 2048-dimensional embedding vector
        
        Args:
            text: The text string to embed
            input_type: 'passage' for docs, 'query' for search
            
        Returns:
            List of 2048 floats representing the embedding
        """
        try:
            response = self.client.embeddings.create(
                input=text,
                model=self.model,
                encoding_format="float",
                extra_body={"input_type": input_type}
            )
            embedding = response.data[0].embedding
            return embedding
        except Exception as e:
            print(f"Error embedding text: {e}")
            raise Exception(f"Failed to generate text embedding: {str(e)}")
    
    def embed_image(self, image_base64: str) -> list[float]:
        """
        Convert a base64-encoded image into a 2048-dimensional embedding vector
        
        Args:
            image_base64: Base64 encoded image string
            
        Returns:
            List of 2048 floats representing the embedding
        """
        try:
            # Format the image for the API
            image_input = f"data:image/jpeg;base64,{image_base64}"
            
            response = self.client.embeddings.create(
                input=image_input,
                model=self.model,
                encoding_format="float",
                extra_body={}  # input_type cause errors for images sometimes
            )
            embedding = response.data[0].embedding
            return embedding
        except Exception as e:
            print(f"Error embedding image: {e}")
            raise Exception(f"Failed to generate image embedding: {str(e)}")


# Singleton instance
embedder = EmbedderService()


if __name__ == "__main__":
    # Simple test
    print("Testing Vextral Embedder Service...")
    test_text = "Hello Vextral - Ask Your Documents"
    
    try:
        embedding = embedder.embed_text(test_text)
        print(f"✓ Text embedding successful")
        print(f"  Vector length: {len(embedding)}")
        print(f"  First 5 values: {embedding[:5]}")
    except Exception as e:
        print(f"✗ Test failed: {e}")
