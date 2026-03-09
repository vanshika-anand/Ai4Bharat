"""
Test script to verify Ollama is working correctly
"""

import httpx
import asyncio
import json

OLLAMA_BASE_URL = "http://localhost:11434"

async def test_ollama():
    client = httpx.AsyncClient(timeout=30.0)
    
    print("🔍 Testing Ollama Connection...\n")
    
    # Test 1: Check if Ollama is running
    try:
        response = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
        if response.status_code == 200:
            print("✅ Ollama is running!")
            models = response.json().get("models", [])
            print(f"   Found {len(models)} models installed:")
            for model in models:
                print(f"   - {model['name']}")
            print()
        else:
            print("❌ Ollama is not responding correctly")
            return
    except Exception as e:
        print(f"❌ Cannot connect to Ollama: {e}")
        print("   Make sure Ollama is running: ollama serve")
        return
    
    # Test 2: Check for required models
    model_names = [m["name"] for m in models]
    
    has_embedding = any("nomic-embed-text" in name for name in model_names)
    has_llm = any("llama3.2" in name or "llama3.1" in name or "mistral" in name for name in model_names)
    
    print("📦 Checking Required Models:")
    if has_embedding:
        print("   ✅ Embedding model found (nomic-embed-text)")
    else:
        print("   ❌ Embedding model not found")
        print("      Run: ollama pull nomic-embed-text")
    
    if has_llm:
        print("   ✅ LLM model found")
    else:
        print("   ⚠️  No LLM model found")
        print("      Run: ollama pull llama3.2")
    print()
    
    if not has_embedding:
        print("⚠️  Cannot proceed without embedding model")
        await client.aclose()
        return
    
    # Test 3: Generate embeddings
    print("🧪 Testing Embeddings...")
    try:
        test_texts = [
            "productivity tips for students",
            "time management strategies",
            "cooking recipes"
        ]
        
        embeddings = []
        for text in test_texts:
            response = await client.post(
                f"{OLLAMA_BASE_URL}/api/embeddings",
                json={"model": "nomic-embed-text", "prompt": text}
            )
            if response.status_code == 200:
                emb = response.json().get("embedding", [])
                embeddings.append(emb)
                print(f"   ✅ Generated embedding for: '{text}' ({len(emb)} dimensions)")
            else:
                print(f"   ❌ Failed to generate embedding for: '{text}'")
        
        # Calculate similarity
        if len(embeddings) == 3:
            import numpy as np
            from sklearn.metrics.pairwise import cosine_similarity
            
            emb1 = np.array(embeddings[0]).reshape(1, -1)
            emb2 = np.array(embeddings[1]).reshape(1, -1)
            emb3 = np.array(embeddings[2]).reshape(1, -1)
            
            sim_12 = cosine_similarity(emb1, emb2)[0][0]
            sim_13 = cosine_similarity(emb1, emb3)[0][0]
            
            print(f"\n   Similarity Analysis:")
            print(f"   - 'productivity tips' vs 'time management': {sim_12*100:.1f}% (should be high)")
            print(f"   - 'productivity tips' vs 'cooking recipes': {sim_13*100:.1f}% (should be low)")
            
            if sim_12 > 0.6 and sim_13 < 0.4:
                print(f"   ✅ Embeddings are working correctly!")
            else:
                print(f"   ⚠️  Unexpected similarity scores")
        
        print()
    except Exception as e:
        print(f"   ❌ Embedding test failed: {e}")
        print()
    
    # Test 4: Test LLM generation (if available)
    if has_llm:
        print("🤖 Testing LLM Generation...")
        try:
            llm_model = None
            for name in model_names:
                if "llama3.2" in name:
                    llm_model = name
                    break
                elif "llama3.1" in name or "mistral" in name:
                    llm_model = name
            
            if llm_model:
                response = await client.post(
                    f"{OLLAMA_BASE_URL}/api/generate",
                    json={
                        "model": llm_model,
                        "prompt": "Write a one-sentence LinkedIn post about productivity.",
                        "stream": False,
                        "options": {"temperature": 0.7}
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    result = response.json().get("response", "")
                    print(f"   ✅ Generated text with {llm_model}:")
                    print(f"   '{result[:200]}...'")
                else:
                    print(f"   ❌ Generation failed")
            print()
        except Exception as e:
            print(f"   ❌ LLM test failed: {e}")
            print()
    
    await client.aclose()
    
    print("\n" + "="*60)
    print("Summary:")
    print("="*60)
    if has_embedding and has_llm:
        print("✅ All systems ready! You can use main_ollama.py")
        print("\nTo start the server:")
        print("   python main_ollama.py")
    elif has_embedding:
        print("⚠️  Embeddings ready, but no LLM for content generation")
        print("   Platform adaptations will use fallback templates")
        print("\nTo add LLM support:")
        print("   ollama pull llama3.2")
    else:
        print("❌ Setup incomplete")
        print("\nRequired steps:")
        print("   1. Make sure Ollama is running: ollama serve")
        print("   2. Pull embedding model: ollama pull nomic-embed-text")
        print("   3. Pull LLM model: ollama pull llama3.2")

if __name__ == "__main__":
    asyncio.run(test_ollama())
