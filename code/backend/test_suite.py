"""
Comprehensive Test Suite for MemoryThread
Tests both Sentence-Transformers and Ollama versions
"""

import asyncio
import httpx
import json
from datetime import datetime
import time

# Configuration
API_BASE_URL = "http://localhost:8000"
TEST_TIMEOUT = 30.0

# Test data
SAMPLE_CONTENTS = [
    {
        "title": "10 Productivity Tips for Students",
        "content": """Productivity is crucial for student success. Here are my top 10 tips:
        
1. Time blocking: Schedule specific times for studying
2. Pomodoro technique: Work in 25-minute focused sessions
3. Eliminate distractions: Turn off notifications
4. Create a dedicated study space
5. Use a planner or digital calendar
6. Break large tasks into smaller chunks
7. Take regular breaks to avoid burnout
8. Get enough sleep - it's essential for memory
9. Exercise regularly to boost energy
10. Review and adjust your methods regularly

These strategies have helped me maintain a 3.8 GPA while working part-time.""",
        "platform": "blog",
        "tags": ["productivity", "study-tips", "time-management"]
    },
    {
        "title": "Time Management Strategies for Busy Professionals",
        "content": """Managing time effectively is the key to professional success. Here's what works:

- Prioritize tasks using the Eisenhower Matrix
- Block time for deep work without interruptions
- Use the two-minute rule: if it takes less than 2 minutes, do it now
- Batch similar tasks together
- Learn to say no to non-essential commitments
- Delegate when possible
- Use automation tools for repetitive tasks
- Review your calendar weekly

Time management isn't about doing more - it's about doing what matters most.""",
        "platform": "linkedin",
        "tags": ["time-management", "productivity", "professional-development"]
    },
    {
        "title": "Best Italian Pasta Recipes",
        "content": """Italian cuisine is all about simple, quality ingredients. Here are my favorite pasta recipes:

Carbonara: Eggs, pecorino cheese, guanciale, and black pepper. No cream!
Cacio e Pepe: Just cheese, pepper, and pasta water
Amatriciana: Tomatoes, guanciale, pecorino
Aglio e Olio: Garlic, olive oil, chili flakes

The secret is using high-quality pasta and not overcooking it. Al dente is essential.
Save pasta water - it's liquid gold for creating silky sauces.""",
        "platform": "blog",
        "tags": ["cooking", "italian-food", "recipes"]
    },
    {
        "title": "Machine Learning Basics for Beginners",
        "content": """Machine learning is transforming technology. Here's what you need to know:

Supervised Learning: Training models with labeled data
- Classification: Predicting categories
- Regression: Predicting continuous values

Unsupervised Learning: Finding patterns in unlabeled data
- Clustering: Grouping similar items
- Dimensionality reduction: Simplifying data

Key concepts:
- Training data vs test data
- Overfitting and underfitting
- Feature engineering
- Model evaluation metrics

Start with scikit-learn in Python - it's beginner-friendly and powerful.""",
        "platform": "blog",
        "tags": ["machine-learning", "ai", "programming", "tutorial"]
    },
    {
        "title": "Effective Study Techniques for Final Exams",
        "content": """Final exams are stressful, but the right study techniques make a huge difference:

Active Recall: Test yourself instead of just re-reading
Spaced Repetition: Review material at increasing intervals
Interleaving: Mix different subjects instead of blocking
Practice Problems: Do as many as possible
Study Groups: Teach others to solidify understanding
Sleep: Don't pull all-nighters - sleep consolidates memory

Create a study schedule 2-3 weeks before exams. Break material into manageable chunks.
Focus on understanding concepts, not memorizing facts.""",
        "platform": "blog",
        "tags": ["study-tips", "exams", "education"]
    }
]

class TestRunner:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=TEST_TIMEOUT)
        self.results = {
            "passed": 0,
            "failed": 0,
            "tests": []
        }
        self.uploaded_content_ids = []
    
    async def run_all_tests(self):
        """Run all test cases"""
        print("=" * 70)
        print("🧪 MEMORYTHREAD TEST SUITE")
        print("=" * 70)
        print()
        
        # Test 1: Health Check
        await self.test_health_check()
        
        # Test 2: Upload Content
        await self.test_upload_content()
        
        # Test 3: List Content
        await self.test_list_content()
        
        # Test 4: Semantic Search
        await self.test_semantic_search()
        
        # Test 5: Repetition Detection
        await self.test_repetition_detection()
        
        # Test 6: Platform Adaptation
        await self.test_platform_adaptation()
        
        # Test 7: Statistics
        await self.test_statistics()
        
        # Print summary
        self.print_summary()
        
        await self.client.aclose()
    
    def log_test(self, name: str, passed: bool, message: str, details: dict = None):
        """Log test result"""
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {name}")
        if message:
            print(f"   {message}")
        if details:
            for key, value in details.items():
                print(f"   {key}: {value}")
        print()
        
        self.results["tests"].append({
            "name": name,
            "passed": passed,
            "message": message,
            "details": details
        })
        
        if passed:
            self.results["passed"] += 1
        else:
            self.results["failed"] += 1
    
    async def test_health_check(self):
        """Test 1: Health Check"""
        print("Test 1: Health Check")
        print("-" * 70)
        
        try:
            response = await self.client.get(f"{API_BASE_URL}/api/health")
            
            if response.status_code == 200:
                data = response.json()
                self.log_test(
                    "Health Check",
                    True,
                    "API is healthy and responding",
                    {
                        "Status": data.get("status"),
                        "Version": data.get("version"),
                        "Total Content": data.get("total_content"),
                        "Ollama Status": data.get("ollama_status", "N/A")
                    }
                )
            else:
                self.log_test(
                    "Health Check",
                    False,
                    f"Unexpected status code: {response.status_code}",
                    None
                )
        except Exception as e:
            self.log_test(
                "Health Check",
                False,
                f"Error: {str(e)}",
                {"Hint": "Make sure the backend is running on port 8000"}
            )
    
    async def test_upload_content(self):
        """Test 2: Upload Content"""
        print("Test 2: Upload Content")
        print("-" * 70)
        
        for idx, content in enumerate(SAMPLE_CONTENTS, 1):
            try:
                start_time = time.time()
                response = await self.client.post(
                    f"{API_BASE_URL}/api/content/upload",
                    json=content
                )
                elapsed = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    content_id = data.get("content_id")
                    self.uploaded_content_ids.append(content_id)
                    
                    self.log_test(
                        f"Upload Content #{idx}: {content['title'][:40]}...",
                        True,
                        "Content uploaded successfully",
                        {
                            "Content ID": content_id,
                            "Word Count": data.get("word_count"),
                            "Embedding Dims": data.get("embedding_dimensions"),
                            "Time": f"{elapsed:.2f}s"
                        }
                    )
                else:
                    self.log_test(
                        f"Upload Content #{idx}",
                        False,
                        f"Upload failed with status {response.status_code}",
                        {"Response": response.text[:200]}
                    )
            except Exception as e:
                self.log_test(
                    f"Upload Content #{idx}",
                    False,
                    f"Error: {str(e)}",
                    None
                )
    
    async def test_list_content(self):
        """Test 3: List Content"""
        print("Test 3: List Content")
        print("-" * 70)
        
        try:
            response = await self.client.get(f"{API_BASE_URL}/api/content/list")
            
            if response.status_code == 200:
                data = response.json()
                self.log_test(
                    "List All Content",
                    True,
                    f"Retrieved {len(data)} content items",
                    {
                        "Total Items": len(data),
                        "Expected": len(SAMPLE_CONTENTS)
                    }
                )
                
                # Test platform filtering
                response = await self.client.get(
                    f"{API_BASE_URL}/api/content/list?platform=blog"
                )
                if response.status_code == 200:
                    blog_data = response.json()
                    self.log_test(
                        "List Content by Platform (blog)",
                        True,
                        f"Retrieved {len(blog_data)} blog posts",
                        {"Blog Posts": len(blog_data)}
                    )
            else:
                self.log_test(
                    "List Content",
                    False,
                    f"Failed with status {response.status_code}",
                    None
                )
        except Exception as e:
            self.log_test(
                "List Content",
                False,
                f"Error: {str(e)}",
                None
            )
    
    async def test_semantic_search(self):
        """Test 4: Semantic Search"""
        print("Test 4: Semantic Search")
        print("-" * 70)
        
        test_queries = [
            {
                "query": "productivity tips",
                "expected_matches": ["Productivity Tips", "Time Management", "Study Techniques"],
                "should_not_match": ["Pasta Recipes"]
            },
            {
                "query": "artificial intelligence and machine learning",
                "expected_matches": ["Machine Learning"],
                "should_not_match": ["Pasta Recipes", "Productivity"]
            },
            {
                "query": "cooking and food",
                "expected_matches": ["Pasta Recipes"],
                "should_not_match": ["Machine Learning", "Productivity"]
            }
        ]
        
        for test in test_queries:
            try:
                start_time = time.time()
                response = await self.client.post(
                    f"{API_BASE_URL}/api/search",
                    json={"query": test["query"], "limit": 5}
                )
                elapsed = time.time() - start_time
                
                if response.status_code == 200:
                    results = response.json()
                    
                    if len(results) > 0:
                        top_result = results[0]
                        similarity = top_result.get("similarity", 0)
                        
                        # Check if semantic matching is working
                        passed = similarity > 50.0  # Should have at least 50% similarity
                        
                        self.log_test(
                            f"Search: '{test['query']}'",
                            passed,
                            f"Found {len(results)} results",
                            {
                                "Top Result": top_result.get("title"),
                                "Similarity": f"{similarity:.1f}%",
                                "Time": f"{elapsed:.2f}s",
                                "Results": [f"{r['title'][:40]} ({r['similarity']:.1f}%)" for r in results[:3]]
                            }
                        )
                    else:
                        self.log_test(
                            f"Search: '{test['query']}'",
                            False,
                            "No results found",
                            None
                        )
                else:
                    self.log_test(
                        f"Search: '{test['query']}'",
                        False,
                        f"Failed with status {response.status_code}",
                        None
                    )
            except Exception as e:
                self.log_test(
                    f"Search: '{test['query']}'",
                    False,
                    f"Error: {str(e)}",
                    None
                )
    
    async def test_repetition_detection(self):
        """Test 5: Repetition Detection"""
        print("Test 5: Repetition Detection")
        print("-" * 70)
        
        test_cases = [
            {
                "name": "High Repetition (should detect)",
                "content": """Productivity is crucial for student success. Here are my top tips:
                Time blocking and scheduling specific times for studying is essential.
                Use the Pomodoro technique with 25-minute focused sessions.
                Eliminate distractions by turning off notifications.""",
                "should_detect": True
            },
            {
                "name": "Moderate Similarity (should detect)",
                "content": """Managing your time well is important for success.
                Here are some strategies: prioritize important tasks, block time for focused work,
                and take regular breaks to maintain productivity.""",
                "should_detect": True
            },
            {
                "name": "Completely Different (should NOT detect)",
                "content": """Quantum computing uses quantum bits or qubits that can exist in
                superposition states. This allows quantum computers to solve certain problems
                exponentially faster than classical computers. Applications include cryptography,
                drug discovery, and optimization problems.""",
                "should_detect": False
            }
        ]
        
        for test in test_cases:
            try:
                start_time = time.time()
                response = await self.client.post(
                    f"{API_BASE_URL}/api/check-repetition",
                    json={"content": test["content"]}
                )
                elapsed = time.time() - start_time
                
                if response.status_code == 200:
                    result = response.json()
                    is_repetition = result.get("is_repetition", False)
                    max_similarity = result.get("max_similarity", 0)
                    
                    # Check if detection matches expectation
                    passed = is_repetition == test["should_detect"]
                    
                    self.log_test(
                        f"Repetition: {test['name']}",
                        passed,
                        result.get("message", ""),
                        {
                            "Detected": "Yes" if is_repetition else "No",
                            "Expected": "Yes" if test["should_detect"] else "No",
                            "Max Similarity": f"{max_similarity:.1f}%",
                            "Similar Items": len(result.get("similar_content", [])),
                            "Time": f"{elapsed:.2f}s"
                        }
                    )
                else:
                    self.log_test(
                        f"Repetition: {test['name']}",
                        False,
                        f"Failed with status {response.status_code}",
                        None
                    )
            except Exception as e:
                self.log_test(
                    f"Repetition: {test['name']}",
                    False,
                    f"Error: {str(e)}",
                    None
                )
    
    async def test_platform_adaptation(self):
        """Test 6: Platform Adaptation"""
        print("Test 6: Platform Adaptation")
        print("-" * 70)
        
        test_content = """Productivity is about working smarter, not harder. 
        Here are three key strategies: prioritize your most important tasks first,
        eliminate distractions during focused work time, and take regular breaks
        to maintain energy and creativity throughout the day."""
        
        try:
            print("   ⏳ Generating adaptations with Llama 3.1 (this may take 30-60s)...")
            start_time = time.time()
            
            # Increase timeout for Llama 3.1 generation
            client = httpx.AsyncClient(timeout=120.0)  # 2 minutes timeout
            response = await client.post(
                f"{API_BASE_URL}/api/adapt-platform",
                json={"content": test_content}
            )
            await client.aclose()
            
            elapsed = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                platforms = ["linkedin", "twitter", "instagram", "tiktok"]
                
                all_present = all(platform in result for platform in platforms)
                all_different = len(set([
                    result[p]["content"][:100] for p in platforms
                ])) == len(platforms)
                
                passed = all_present and all_different
                
                details = {
                    "Time": f"{elapsed:.2f}s",
                    "Original Length": result.get("original_length", 0)
                }
                
                for platform in platforms:
                    if platform in result:
                        content_len = len(result[platform]["content"])
                        details[f"{platform.capitalize()} Length"] = f"{content_len} chars"
                
                self.log_test(
                    "Platform Adaptation",
                    passed,
                    "Generated adaptations for all platforms",
                    details
                )
                
                # Show sample output
                print("   Sample LinkedIn Output:")
                print(f"   {result['linkedin']['content'][:150]}...")
                print()
                
            else:
                self.log_test(
                    "Platform Adaptation",
                    False,
                    f"Failed with status {response.status_code}",
                    None
                )
        except Exception as e:
            self.log_test(
                "Platform Adaptation",
                False,
                f"Error: {str(e)}",
                {"Note": "If using Ollama, make sure models are pulled"}
            )
    
    async def test_statistics(self):
        """Test 7: Statistics"""
        print("Test 7: Statistics")
        print("-" * 70)
        
        try:
            response = await self.client.get(f"{API_BASE_URL}/api/stats")
            
            if response.status_code == 200:
                stats = response.json()
                
                self.log_test(
                    "Statistics",
                    True,
                    "Retrieved system statistics",
                    {
                        "Total Content": stats.get("total_content", 0),
                        "Total Words": stats.get("total_words", 0),
                        "Avg Words/Content": f"{stats.get('avg_words_per_content', 0):.0f}",
                        "Platform Breakdown": json.dumps(stats.get("platform_breakdown", {}))
                    }
                )
            else:
                self.log_test(
                    "Statistics",
                    False,
                    f"Failed with status {response.status_code}",
                    None
                )
        except Exception as e:
            self.log_test(
                "Statistics",
                False,
                f"Error: {str(e)}",
                None
            )
    
    def print_summary(self):
        """Print test summary"""
        print("=" * 70)
        print("📊 TEST SUMMARY")
        print("=" * 70)
        print()
        
        total = self.results["passed"] + self.results["failed"]
        pass_rate = (self.results["passed"] / total * 100) if total > 0 else 0
        
        print(f"Total Tests: {total}")
        print(f"✅ Passed: {self.results['passed']}")
        print(f"❌ Failed: {self.results['failed']}")
        print(f"Pass Rate: {pass_rate:.1f}%")
        print()
        
        if self.results["failed"] > 0:
            print("Failed Tests:")
            for test in self.results["tests"]:
                if not test["passed"]:
                    print(f"  - {test['name']}: {test['message']}")
            print()
        
        if pass_rate == 100:
            print("🎉 ALL TESTS PASSED! Your MemoryThread is working perfectly!")
        elif pass_rate >= 80:
            print("✅ Most tests passed. Check failed tests above.")
        else:
            print("⚠️  Many tests failed. Please check your setup.")
        
        print()
        print("=" * 70)

async def main():
    """Main test runner"""
    runner = TestRunner()
    await runner.run_all_tests()

if __name__ == "__main__":
    print()
    print("Starting MemoryThread Test Suite...")
    print("Make sure the backend is running on http://localhost:8000")
    print()
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
    except Exception as e:
        print(f"\n\nFatal error: {e}")
