"""
Generate a visual HTML test report
"""

import asyncio
import httpx
import json
from datetime import datetime
import time

API_BASE_URL = "http://localhost:8000"

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>MemoryThread Test Report</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        .container {
            background: white;
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }
        h1 {
            color: #667eea;
            margin-bottom: 10px;
        }
        .timestamp {
            color: #666;
            font-size: 14px;
            margin-bottom: 30px;
        }
        .summary {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }
        .stat-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
        }
        .stat-value {
            font-size: 36px;
            font-weight: bold;
            margin: 10px 0;
        }
        .stat-label {
            font-size: 14px;
            opacity: 0.9;
        }
        .test-section {
            margin-bottom: 30px;
        }
        .test-section h2 {
            color: #333;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }
        .test-item {
            background: #f8f9fa;
            border-left: 4px solid #ddd;
            padding: 15px;
            margin-bottom: 15px;
            border-radius: 5px;
        }
        .test-item.pass {
            border-left-color: #28a745;
            background: #d4edda;
        }
        .test-item.fail {
            border-left-color: #dc3545;
            background: #f8d7da;
        }
        .test-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }
        .test-name {
            font-weight: bold;
            color: #333;
        }
        .test-status {
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: bold;
        }
        .test-status.pass {
            background: #28a745;
            color: white;
        }
        .test-status.fail {
            background: #dc3545;
            color: white;
        }
        .test-details {
            color: #666;
            font-size: 14px;
            margin-top: 10px;
        }
        .test-details dt {
            font-weight: bold;
            margin-top: 5px;
        }
        .test-details dd {
            margin-left: 20px;
            margin-bottom: 5px;
        }
        .progress-bar {
            width: 100%;
            height: 30px;
            background: #e9ecef;
            border-radius: 15px;
            overflow: hidden;
            margin: 20px 0;
        }
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #28a745, #20c997);
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
            transition: width 0.3s ease;
        }
        .footer {
            text-align: center;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            color: #666;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🧪 MemoryThread Test Report</h1>
        <div class="timestamp">Generated: {timestamp}</div>
        
        <div class="summary">
            <div class="stat-card">
                <div class="stat-label">Total Tests</div>
                <div class="stat-value">{total_tests}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Passed</div>
                <div class="stat-value">{passed_tests}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Failed</div>
                <div class="stat-value">{failed_tests}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Pass Rate</div>
                <div class="stat-value">{pass_rate}%</div>
            </div>
        </div>
        
        <div class="progress-bar">
            <div class="progress-fill" style="width: {pass_rate}%">
                {pass_rate}% Complete
            </div>
        </div>
        
        {test_sections}
        
        <div class="footer">
            <p>MemoryThread v3.0 - AI for Bharat Hackathon 2026</p>
            <p>Backend: {backend_version} | Ollama: {ollama_status}</p>
        </div>
    </div>
</body>
</html>
"""

async def run_tests_and_generate_report():
    """Run tests and generate HTML report"""
    client = httpx.AsyncClient(timeout=30.0)
    results = []
    
    print("Running tests and generating report...")
    print()
    
    # Test 1: Health Check
    try:
        response = await client.get(f"{API_BASE_URL}/api/health")
        data = response.json()
        results.append({
            "name": "Health Check",
            "passed": response.status_code == 200,
            "details": {
                "Status": data.get("status"),
                "Version": data.get("version"),
                "Ollama": data.get("ollama_status", "N/A")
            }
        })
        backend_version = data.get("version", "Unknown")
        ollama_status = data.get("ollama_status", "N/A")
    except Exception as e:
        results.append({
            "name": "Health Check",
            "passed": False,
            "details": {"Error": str(e)}
        })
        backend_version = "Unknown"
        ollama_status = "Unknown"
    
    # Test 2: Upload
    try:
        start = time.time()
        response = await client.post(
            f"{API_BASE_URL}/api/content/upload",
            json={
                "title": "Test: Productivity Tips",
                "content": "Time management and productivity are essential skills. Here are some tips: prioritize tasks, eliminate distractions, take breaks.",
                "platform": "blog"
            }
        )
        elapsed = time.time() - start
        results.append({
            "name": "Content Upload",
            "passed": response.status_code == 200,
            "details": {
                "Time": f"{elapsed:.3f}s",
                "Status": response.status_code
            }
        })
    except Exception as e:
        results.append({
            "name": "Content Upload",
            "passed": False,
            "details": {"Error": str(e)}
        })
    
    # Test 3: Search
    try:
        start = time.time()
        response = await client.post(
            f"{API_BASE_URL}/api/search",
            json={"query": "productivity", "limit": 5}
        )
        elapsed = time.time() - start
        data = response.json()
        results.append({
            "name": "Semantic Search",
            "passed": response.status_code == 200 and len(data) > 0,
            "details": {
                "Results Found": len(data),
                "Time": f"{elapsed:.3f}s",
                "Top Result": data[0]["title"] if data else "None"
            }
        })
    except Exception as e:
        results.append({
            "name": "Semantic Search",
            "passed": False,
            "details": {"Error": str(e)}
        })
    
    # Test 4: Repetition Check
    try:
        start = time.time()
        response = await client.post(
            f"{API_BASE_URL}/api/check-repetition",
            json={"content": "Time management and productivity tips for students"}
        )
        elapsed = time.time() - start
        data = response.json()
        results.append({
            "name": "Repetition Detection",
            "passed": response.status_code == 200,
            "details": {
                "Detected": "Yes" if data.get("is_repetition") else "No",
                "Max Similarity": f"{data.get('max_similarity', 0):.1f}%",
                "Time": f"{elapsed:.3f}s"
            }
        })
    except Exception as e:
        results.append({
            "name": "Repetition Detection",
            "passed": False,
            "details": {"Error": str(e)}
        })
    
    # Test 5: Platform Adaptation
    try:
        start = time.time()
        response = await client.post(
            f"{API_BASE_URL}/api/adapt-platform",
            json={"content": "Productivity tips: prioritize tasks, eliminate distractions, take breaks."}
        )
        elapsed = time.time() - start
        data = response.json()
        results.append({
            "name": "Platform Adaptation",
            "passed": response.status_code == 200 and "linkedin" in data,
            "details": {
                "Platforms": "LinkedIn, Twitter, Instagram, TikTok",
                "Time": f"{elapsed:.3f}s"
            }
        })
    except Exception as e:
        results.append({
            "name": "Platform Adaptation",
            "passed": False,
            "details": {"Error": str(e)}
        })
    
    await client.aclose()
    
    # Generate HTML
    passed = sum(1 for r in results if r["passed"])
    failed = len(results) - passed
    pass_rate = int((passed / len(results)) * 100) if results else 0
    
    test_sections_html = ""
    for result in results:
        status_class = "pass" if result["passed"] else "fail"
        status_text = "PASS" if result["passed"] else "FAIL"
        
        details_html = "<dl class='test-details'>"
        for key, value in result["details"].items():
            details_html += f"<dt>{key}:</dt><dd>{value}</dd>"
        details_html += "</dl>"
        
        test_sections_html += f"""
        <div class="test-item {status_class}">
            <div class="test-header">
                <span class="test-name">{result['name']}</span>
                <span class="test-status {status_class}">{status_text}</span>
            </div>
            {details_html}
        </div>
        """
    
    html = HTML_TEMPLATE.format(
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        total_tests=len(results),
        passed_tests=passed,
        failed_tests=failed,
        pass_rate=pass_rate,
        test_sections=test_sections_html,
        backend_version=backend_version,
        ollama_status=ollama_status
    )
    
    # Save report
    report_path = "test_report.html"
    with open(report_path, "w") as f:
        f.write(html)
    
    print(f"✅ Test report generated: {report_path}")
    print(f"📊 Results: {passed}/{len(results)} tests passed ({pass_rate}%)")
    print()
    print(f"Open the report: open {report_path}")
    
    return pass_rate == 100

if __name__ == "__main__":
    success = asyncio.run(run_tests_and_generate_report())
    exit(0 if success else 1)
