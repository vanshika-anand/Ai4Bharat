"""
Test Knowledge Graph Integration
Quick test to verify knowledge extraction and repetition detection
"""

import asyncio
import httpx
import json

API_URL = "http://localhost:8000/api"

async def test_knowledge_graph():
    """Test the knowledge graph functionality"""
    
    print("=" * 70)
    print("🧠 KNOWLEDGE GRAPH TEST SUITE")
    print("=" * 70)
    print()
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        
        # Test 1: Upload content with knowledge extraction
        print("Test 1: Upload Content with Knowledge Extraction")
        print("-" * 70)
        
        test_content = {
            "title": "Machine Learning Fundamentals",
            "content": """
            Machine learning is a subset of artificial intelligence that enables computers to learn from data.
            Key concepts include neural networks, deep learning, and supervised learning.
            Popular frameworks like TensorFlow and PyTorch make it easier to build ML models.
            Data preprocessing and feature engineering are crucial steps in the ML pipeline.
            """,
            "platform": "blog",
            "tags": ["AI", "ML", "tech"]
        }
        
        response = await client.post(f"{API_URL}/content/upload", json=test_content)
        if response.status_code == 200:
            data = response.json()
            content_id = data['content_id']
            print(f"✅ Content uploaded: ID {content_id}")
            print(f"   Word count: {data['word_count']}")
            print(f"   Embedding dims: {data['embedding_dimensions']}")
            print()
            
            # Manually trigger knowledge extraction to ensure it completes
            print("⏳ Triggering knowledge extraction...")
            extract_response = await client.post(f"{API_URL}/knowledge/extract/{content_id}")
            if extract_response.status_code == 200:
                print("✅ Knowledge extraction completed")
            else:
                print(f"⚠️  Knowledge extraction returned: {extract_response.status_code}")
            print()
            
            # Test 2: Get knowledge graph
            print("\nTest 2: Get Knowledge Graph")
            print("-" * 70)
            
            response = await client.get(f"{API_URL}/knowledge/graph/{content_id}")
            if response.status_code == 200:
                graph = response.json()
                entities = graph['graph']['entities']
                topics = graph['graph']['topics']
                
                print(f"✅ Knowledge graph retrieved")
                print(f"   Entities found: {len(entities)}")
                if entities:
                    print("   Sample entities:")
                    for entity in entities[:5]:
                        print(f"      - {entity['name']} ({entity['type']})")
                
                print(f"   Topics found: {len(topics)}")
                if topics:
                    print("   Sample topics:")
                    for topic in topics[:5]:
                        print(f"      - {topic['name']}")
                print()
            else:
                print(f"❌ Failed to get knowledge graph: {response.status_code}")
                print()
            
            # Test 3: Check repetition with embeddings
            print("Test 3: Check Repetition (Embeddings)")
            print("-" * 70)
            
            draft = """
            Deep learning is an advanced form of machine learning using neural networks.
            TensorFlow and PyTorch are the most popular frameworks for building deep learning models.
            Data preprocessing is essential for model training.
            """
            
            response = await client.post(
                f"{API_URL}/check-repetition",
                json={"content": draft}
            )
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Embedding check complete")
                print(f"   Is repetition: {result['is_repetition']}")
                print(f"   Max similarity: {result['max_similarity']:.1f}%")
                print(f"   Message: {result['message']}")
                print()
            else:
                print(f"❌ Embedding check failed: {response.status_code}")
                print()
            
            # Test 4: Check repetition with knowledge graph
            print("Test 4: Check Repetition (Knowledge Graph)")
            print("-" * 70)
            
            response = await client.post(
                f"{API_URL}/check-repetition-graph",
                json={"content": draft}
            )
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Knowledge graph check complete")
                print(f"   Is repetition: {result['is_repetition']}")
                print(f"   Max similarity: {result.get('max_similarity', 0):.1f}%")
                print(f"   Message: {result['message']}")
                
                if result.get('graph_analysis'):
                    analysis = result['graph_analysis']
                    print(f"\n   📊 Analysis:")
                    print(f"      Entities extracted: {analysis.get('total_entities_found', 0)}")
                    print(f"      Topics extracted: {analysis.get('total_topics_found', 0)}")
                    
                    if analysis.get('draft_entities'):
                        print(f"      Sample entities: {', '.join(analysis['draft_entities'][:5])}")
                    if analysis.get('draft_topics'):
                        print(f"      Sample topics: {', '.join(analysis['draft_topics'][:5])}")
                
                if result.get('similar_content'):
                    print(f"\n   🔍 Similar content found: {len(result['similar_content'])}")
                    for item in result['similar_content'][:2]:
                        print(f"      - {item['title']} ({item['similarity']:.1f}% similar)")
                        if item.get('shared_entities'):
                            print(f"        Shared entities: {', '.join(item['shared_entities'][:3])}")
                        if item.get('shared_topics'):
                            print(f"        Shared topics: {', '.join(item['shared_topics'][:3])}")
                print()
            else:
                print(f"❌ Knowledge graph check failed: {response.status_code}")
                print()
            
            # Test 5: Find related content
            print("Test 5: Find Related Content")
            print("-" * 70)
            
            response = await client.get(f"{API_URL}/knowledge/related/{content_id}?limit=5")
            if response.status_code == 200:
                related = response.json()
                if len(related) > 0:
                    print(f"✅ Related content found: {len(related)}")
                    for item in related[:3]:
                        print(f"   - {item['title']}")
                        print(f"     Shared entities: {item['shared_entities']}, Shared topics: {item['shared_topics']}")
                        print(f"     Relevance score: {item['relevance_score']:.2f}")
                else:
                    print(f"✅ No related content found (expected - only 1 content item)")
                print()
            else:
                print(f"❌ Failed to find related content: {response.status_code}")
                print()
            
            # Test 6: Upload different content
            print("Test 6: Upload Different Content (Italian Pasta)")
            print("-" * 70)
            
            pasta_content = {
                "title": "Italian Pasta Recipes",
                "content": """
                Italian cuisine is famous for its delicious pasta dishes. Classic recipes include 
                carbonara, amatriciana, and cacio e pepe. Fresh ingredients like Parmigiano-Reggiano 
                cheese and guanciale are essential for authentic flavor. Proper pasta cooking requires 
                salted boiling water and al dente texture.
                """,
                "platform": "blog",
                "tags": ["food", "cooking"]
            }
            
            response = await client.post(f"{API_URL}/content/upload", json=pasta_content)
            if response.status_code == 200:
                data = response.json()
                pasta_id = data['content_id']
                print(f"✅ Pasta content uploaded: ID {pasta_id}")
                
                # Extract knowledge
                extract_response = await client.post(f"{API_URL}/knowledge/extract/{pasta_id}")
                if extract_response.status_code == 200:
                    print("✅ Knowledge extraction completed")
                print()
            else:
                print(f"❌ Upload failed: {response.status_code}")
                print()
            
            # Test 7: Check ML draft against pasta content
            print("Test 7: Check ML Draft Against Pasta Content")
            print("-" * 70)
            
            response = await client.post(
                f"{API_URL}/check-repetition-graph",
                json={"content": draft}
            )
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Knowledge graph check complete")
                print(f"   Is repetition: {result['is_repetition']}")
                
                if result.get('similar_content'):
                    print(f"   Similar items found: {len(result['similar_content'])}")
                    for item in result['similar_content']:
                        print(f"      - {item['title']} ({item['similarity']:.1f}% similar)")
                else:
                    print(f"   ✅ No overlap between ML and Pasta content (as expected!)")
                print()
            else:
                print(f"❌ Check failed: {response.status_code}")
                print()
            
            # Test 8: Summary comparison
            print("Test 8: Summary - Embeddings vs Knowledge Graph")
            print("-" * 70)
            
            ml_draft = """
            Machine Learning and Deep Learning are powerful AI techniques. Neural Networks 
            form the foundation of modern ML systems. Popular frameworks include TensorFlow 
            and PyTorch for building models. Data Preprocessing and Feature Engineering are 
            essential steps in any ML pipeline.
            """
            
            # Embeddings check
            emb_response = await client.post(
                f"{API_URL}/check-repetition",
                json={"content": ml_draft}
            )
            
            # Knowledge graph check
            kg_response = await client.post(
                f"{API_URL}/check-repetition-graph",
                json={"content": ml_draft}
            )
            
            if emb_response.status_code == 200 and kg_response.status_code == 200:
                emb_result = emb_response.json()
                kg_result = kg_response.json()
                
                print("📊 EMBEDDINGS APPROACH:")
                print(f"   Similarity: {emb_result['max_similarity']:.1f}%")
                print(f"   Message: {emb_result['message']}")
                print(f"   Explanation: None (black box)")
                print()
                
                print("🧠 KNOWLEDGE GRAPH APPROACH:")
                print(f"   Similarity: {kg_result.get('max_similarity', 0):.1f}%")
                print(f"   Message: {kg_result['message']}")
                if kg_result.get('similar_content') and len(kg_result['similar_content']) > 0:
                    item = kg_result['similar_content'][0]
                    if item.get('shared_entities'):
                        print(f"   Shared Entities ({len(item['shared_entities'])}): {', '.join(item['shared_entities'][:5])}")
                    if item.get('shared_topics'):
                        print(f"   Shared Topics ({len(item['shared_topics'])}): {', '.join(item['shared_topics'][:3])}")
                    if 'entity_overlap' in item:
                        print(f"   Entity Overlap: {item['entity_overlap']:.1f}%")
                    if 'topic_overlap' in item:
                        print(f"   Topic Overlap: {item['topic_overlap']:.1f}%")
                print()
                
                print("💡 KEY DIFFERENCE:")
                print("   Embeddings: Fast but unexplainable")
                print("   Knowledge Graph: Explainable with specific shared elements")
                print()
            else:
                print(f"❌ Comparison failed")
                print()
            
        else:
            print(f"❌ Upload failed: {response.status_code}")
            print()
    
    print("=" * 70)
    print("✅ KNOWLEDGE GRAPH TESTS COMPLETE")
    print("=" * 70)

if __name__ == "__main__":
    print("\nStarting Knowledge Graph Test Suite...")
    print("Make sure the backend is running on http://localhost:8000\n")
    
    try:
        asyncio.run(test_knowledge_graph())
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test failed with error: {e}")
