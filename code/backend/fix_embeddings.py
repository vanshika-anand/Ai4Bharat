"""
Fix embeddings in database - regenerate all embeddings with current model
"""

import asyncio
import sqlite3
import json
import httpx
from pathlib import Path

DB_PATH = Path("memorythread.db")
OLLAMA_BASE_URL = "http://localhost:11434"
EMBEDDING_MODEL = "nomic-embed-text"

async def regenerate_embeddings():
    """Regenerate all embeddings with Ollama"""
    
    print("🔧 Fixing Embeddings Database")
    print("=" * 60)
    print()
    
    # Check Ollama
    client = httpx.AsyncClient(timeout=30.0)
    try:
        response = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
        if response.status_code != 200:
            print("❌ Ollama is not running")
            print("   Start it with: ollama serve")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to Ollama: {e}")
        print("   Start it with: ollama serve")
        return False
    
    print("✅ Ollama is running")
    print()
    
    # Get all content
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute('SELECT id, content FROM content')
    rows = c.fetchall()
    
    if not rows:
        print("No content found in database")
        conn.close()
        await client.aclose()
        return True
    
    print(f"Found {len(rows)} content items")
    print("Regenerating embeddings...")
    print()
    
    success_count = 0
    error_count = 0
    
    for content_id, content_text in rows:
        try:
            # Generate new embedding with Ollama
            response = await client.post(
                f"{OLLAMA_BASE_URL}/api/embeddings",
                json={
                    "model": EMBEDDING_MODEL,
                    "prompt": content_text
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                embedding = data.get("embedding", [])
                
                # Normalize
                import numpy as np
                embedding = np.array(embedding)
                norm = np.linalg.norm(embedding)
                if norm > 0:
                    embedding = embedding / norm
                
                # Update or insert embedding
                c.execute(
                    'SELECT id FROM embeddings WHERE content_id = ?',
                    (content_id,)
                )
                existing = c.fetchone()
                
                if existing:
                    c.execute(
                        'UPDATE embeddings SET embedding = ?, model_version = ? WHERE content_id = ?',
                        (json.dumps(embedding.tolist()), 'ollama-nomic', content_id)
                    )
                else:
                    c.execute(
                        'INSERT INTO embeddings (content_id, embedding, model_version) VALUES (?, ?, ?)',
                        (content_id, json.dumps(embedding.tolist()), 'ollama-nomic')
                    )
                
                success_count += 1
                print(f"✅ Content ID {content_id}: {len(embedding)} dimensions")
            else:
                print(f"❌ Content ID {content_id}: Failed to generate embedding")
                error_count += 1
        
        except Exception as e:
            print(f"❌ Content ID {content_id}: Error - {e}")
            error_count += 1
    
    conn.commit()
    conn.close()
    await client.aclose()
    
    print()
    print("=" * 60)
    print(f"✅ Successfully regenerated: {success_count}")
    if error_count > 0:
        print(f"❌ Errors: {error_count}")
    print("=" * 60)
    print()
    
    if error_count == 0:
        print("🎉 All embeddings fixed! You can now run tests again.")
        return True
    else:
        print("⚠️  Some embeddings failed. Check errors above.")
        return False

if __name__ == "__main__":
    print()
    success = asyncio.run(regenerate_embeddings())
    print()
    
    if success:
        print("Next steps:")
        print("  1. Run tests again: python test_suite.py")
        print("  2. All tests should pass now!")
    else:
        print("Troubleshooting:")
        print("  1. Make sure Ollama is running: ollama serve")
        print("  2. Make sure model is pulled: ollama pull nomic-embed-text")
        print("  3. Try again")
