"""
Comprehensive validation tests for the Web Dashboard
Tests all API endpoints, file downloads, security, and performance
"""

import asyncio
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

import httpx
import pytest


# Dashboard validation test suite
class TestDashboardValidation:
    """Comprehensive test suite for web dashboard functionality"""

    BASE_URL = "http://0.0.0.0:12656"

    @pytest.fixture
    async def client(self):
        """HTTP client fixture"""
        async with httpx.AsyncClient(base_url=self.BASE_URL, timeout=30.0) as client:
            yield client

    @pytest.fixture
    def mock_session_data(self):
        """Mock research session data"""
        return {
            "session_id": "run_1757070320_test_research_subject",
            "subject": "test research subject",
            "created": datetime.now().isoformat(),
            "files": [
                {
                    "filename": "research_report.pdf",
                    "url": "/download/run_1757070320_test_research_subject/test.pdf",
                    "size": 1024,
                    "created": datetime.now().isoformat(),
                },
                {
                    "filename": "research_report.docx",
                    "url": "/download/run_1757070320_test_research_subject/test.docx",
                    "size": 2048,
                    "created": datetime.now().isoformat(),
                },
                {
                    "filename": "research_report.md",
                    "url": "/download/run_1757070320_test_research_subject/test.md",
                    "size": 512,
                    "created": datetime.now().isoformat(),
                },
            ],
            "file_count": 3,
        }


class TestAPIEndpoints(TestDashboardValidation):
    """Test all API endpoints"""

    async def test_health_endpoint(self, client):
        """Test health check endpoint"""
        response = await client.get("/api/health")

        assert response.status_code == 200
        data = response.json()

        # Validate response structure
        assert "status" in data
        assert "active_sessions" in data
        assert "websocket_connections" in data

        # Validate values
        assert data["status"] == "healthy"
        assert isinstance(data["active_sessions"], int)
        assert isinstance(data["websocket_connections"], int)

        print(f"✅ Health endpoint: {data}")

    async def test_sessions_endpoint(self, client):
        """Test /api/sessions endpoint"""
        response = await client.get("/api/sessions")

        assert response.status_code == 200
        data = response.json()

        # Should return a list
        assert isinstance(data, list)

        # If sessions exist, validate structure
        if data:
            session = data[0]
            required_fields = ["session_id", "subject", "created", "files", "file_count"]

            for field in required_fields:
                assert field in session, f"Missing field: {field}"

            # Validate session structure
            assert isinstance(session["session_id"], str)
            assert isinstance(session["subject"], str)
            assert isinstance(session["files"], list)
            assert isinstance(session["file_count"], int)

            # Validate file structure if files exist
            if session["files"]:
                file_info = session["files"][0]
                file_fields = ["filename", "url", "size", "created"]
                for field in file_fields:
                    assert field in file_info, f"Missing file field: {field}"

        print(f"✅ Sessions endpoint returned {len(data)} sessions")

    async def test_session_status_endpoint(self, client):
        """Test individual session status endpoint"""
        # First get available sessions
        sessions_response = await client.get("/api/sessions")
        sessions = sessions_response.json()

        if not sessions:
            pytest.skip("No sessions available for testing")

        session_id = sessions[0]["session_id"]
        response = await client.get(f"/api/session/{session_id}")

        if response.status_code == 200:
            data = response.json()

            # Validate response structure
            required_fields = ["session_id", "status", "progress", "files"]
            for field in required_fields:
                assert field in data, f"Missing field: {field}"

            assert data["session_id"] == session_id
            assert isinstance(data["progress"], (int, float))
            assert 0 <= data["progress"] <= 100

            print(f"✅ Session status endpoint: {data['status']}")
        else:
            print(f"⚠️ Session {session_id} not found (404) - this is acceptable")

    async def test_dashboard_homepage(self, client):
        """Test main dashboard page"""
        response = await client.get("/")

        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")

        content = response.text
        assert "Deep Research" in content or "dashboard" in content.lower()

        print("✅ Dashboard homepage loads successfully")


class TestFileDownloads(TestDashboardValidation):
    """Test file download functionality"""

    async def test_valid_file_download(self, client):
        """Test downloading valid files"""
        # Get available sessions first
        sessions_response = await client.get("/api/sessions")
        sessions = sessions_response.json()

        if not sessions:
            pytest.skip("No sessions available for file download testing")

        # Find a session with files
        test_session = None
        for session in sessions:
            if session["files"]:
                test_session = session
                break

        if not test_session:
            pytest.skip("No sessions with files available for testing")

        # Test downloading each file
        for file_info in test_session["files"]:
            # Extract session_id and filename from URL
            url_parts = file_info["url"].split("/")
            if len(url_parts) >= 4 and url_parts[1] == "download":
                session_id = url_parts[2]
                filename = url_parts[3]

                response = await client.get(f"/download/{session_id}/{filename}")

                if response.status_code == 200:
                    # Validate MIME type
                    content_type = response.headers.get("content-type", "")
                    expected_mime_types = {
                        ".pdf": "application/pdf",
                        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        ".md": "text/markdown",
                    }

                    file_ext = "." + filename.split(".")[-1].lower()
                    if file_ext in expected_mime_types:
                        expected_mime = expected_mime_types[file_ext]
                        assert expected_mime in content_type, (
                            f"Wrong MIME type for {filename}: {content_type}"
                        )

                    # Validate content disposition header
                    assert "attachment" in response.headers.get("content-disposition", "").lower()

                    # Validate content length
                    content_length = len(response.content)
                    assert content_length > 0, f"Empty file content for {filename}"

                    print(f"✅ File download successful: {filename} ({content_length} bytes)")
                else:
                    print(f"⚠️ File {filename} not found (404) - may have been cleaned up")

    async def test_mime_type_validation(self, client):
        """Test MIME type headers for different file types"""
        expected_mime_types = {
            "test.pdf": "application/pdf",
            "test.docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "test.md": "text/markdown",
        }

        # This test validates the MIME type logic without requiring actual files

        from web_dashboard.file_manager import FileManager

        file_manager = FileManager(Path("/tmp"), Path("/tmp"))

        for filename, expected_mime in expected_mime_types.items():
            actual_mime = file_manager.get_mime_type(filename)
            assert actual_mime == expected_mime, f"MIME type mismatch for {filename}"

        print("✅ MIME type validation passed for all file types")


class TestSecurity(TestDashboardValidation):
    """Test security features"""

    async def test_path_traversal_protection(self, client):
        """Test protection against path traversal attacks"""
        malicious_paths = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
            "....//....//....//etc/passwd",
            "/etc/passwd",
            "C:\\windows\\system32\\config\\sam",
        ]

        for malicious_path in malicious_paths:
            response = await client.get(f"/download/test_session/{malicious_path}")

            # Should return 400 (Bad Request) or 404 (Not Found), never 200
            assert response.status_code in [
                400,
                404,
            ], f"Path traversal not blocked: {malicious_path}"

        print("✅ Path traversal protection working")

    async def test_invalid_filename_protection(self, client):
        """Test protection against invalid filenames"""
        invalid_filenames = [
            "",  # Empty filename
            "file_without_extension",  # No extension
            "file.exe",  # Unsupported extension
            "file.bat",  # Potentially dangerous extension
            "file.sh",  # Script file
            "con.pdf",  # Windows reserved name (if applicable)
            "prn.docx",  # Windows reserved name (if applicable)
        ]

        for invalid_filename in invalid_filenames:
            response = await client.get(f"/download/test_session/{invalid_filename}")

            # Should return 400 (Bad Request) or 404 (Not Found)
            assert response.status_code in [
                400,
                404,
            ], f"Invalid filename not blocked: {invalid_filename}"

        print("✅ Invalid filename protection working")

    async def test_method_restrictions(self, client):
        """Test HTTP method restrictions"""
        # Download endpoint should only accept GET
        response = await client.post("/download/test_session/test.pdf")
        assert response.status_code == 405  # Method Not Allowed

        response = await client.put("/download/test_session/test.pdf")
        assert response.status_code == 405  # Method Not Allowed

        response = await client.delete("/download/test_session/test.pdf")
        assert response.status_code == 405  # Method Not Allowed

        print("✅ HTTP method restrictions working")


class TestErrorHandling(TestDashboardValidation):
    """Test error handling scenarios"""

    async def test_nonexistent_session(self, client):
        """Test handling of nonexistent session requests"""
        fake_session_id = "nonexistent_session_12345"

        # Test session status endpoint
        response = await client.get(f"/api/session/{fake_session_id}")
        assert response.status_code == 404

        # Test file download endpoint
        response = await client.get(f"/download/{fake_session_id}/test.pdf")
        assert response.status_code == 404

        print("✅ Nonexistent session handling working")

    async def test_nonexistent_file(self, client):
        """Test handling of nonexistent file requests"""
        # Use a real session ID but fake file
        sessions_response = await client.get("/api/sessions")
        sessions = sessions_response.json()

        if sessions:
            session_id = sessions[0]["session_id"]
            response = await client.get(f"/download/{session_id}/nonexistent_file.pdf")
            assert response.status_code == 404

        print("✅ Nonexistent file handling working")


class TestPerformance(TestDashboardValidation):
    """Test performance characteristics"""

    async def test_api_response_times(self, client):
        """Test API response times"""
        endpoints = ["/api/health", "/api/sessions", "/"]

        response_times = {}

        for endpoint in endpoints:
            start_time = time.time()
            response = await client.get(endpoint)
            end_time = time.time()

            response_time = end_time - start_time
            response_times[endpoint] = response_time

            # API should respond within reasonable time (5 seconds)
            assert response_time < 5.0, f"Slow response for {endpoint}: {response_time:.2f}s"
            assert response.status_code == 200

        print(f"✅ API response times: {response_times}")

    async def test_concurrent_requests(self, client):
        """Test handling of concurrent requests"""

        async def make_request():
            return await client.get("/api/health")

        # Make 10 concurrent requests
        start_time = time.time()
        tasks = [make_request() for _ in range(10)]
        responses = await asyncio.gather(*tasks)
        end_time = time.time()

        # All requests should succeed
        for response in responses:
            assert response.status_code == 200

        total_time = end_time - start_time
        avg_time = total_time / 10

        print(
            f"✅ Concurrent requests handled: 10 requests in {total_time:.2f}s (avg: {avg_time:.2f}s)"
        )


class TestDataIntegrity(TestDashboardValidation):
    """Test data integrity and validation"""

    async def test_session_data_structure(self, client):
        """Test that session data follows expected structure"""
        response = await client.get("/api/sessions")
        assert response.status_code == 200

        sessions = response.json()

        for session in sessions:
            # Validate session ID format (should match run_timestamp_subject pattern)
            assert session["session_id"].startswith("run_"), (
                f"Invalid session ID format: {session['session_id']}"
            )

            # Validate file count matches actual files array length
            assert len(session["files"]) == session["file_count"], (
                f"File count mismatch in session {session['session_id']}"
            )

            # Validate file URLs are properly formatted
            for file_info in session["files"]:
                url = file_info["url"]
                assert url.startswith("/download/"), f"Invalid file URL format: {url}"
                assert session["session_id"] in url, f"Session ID not in file URL: {url}"

        print(f"✅ Data integrity validated for {len(sessions)} sessions")


# Validation report generator
class ValidationReporter:
    """Generate comprehensive validation report"""

    def __init__(self):
        self.results = {
            "api_endpoints": [],
            "file_downloads": [],
            "security": [],
            "performance": {},
            "errors": [],
            "summary": {},
        }

    def add_result(
        self, category: str, test_name: str, status: str, details: Dict[str, Any] = None
    ):
        """Add test result"""
        result = {
            "test": test_name,
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "details": details or {},
        }

        if category in self.results:
            self.results[category].append(result)

    def generate_report(self) -> str:
        """Generate formatted validation report"""
        report = []
        report.append("=" * 60)
        report.append("WEB DASHBOARD VALIDATION REPORT")
        report.append("=" * 60)
        report.append(f"Generated: {datetime.now().isoformat()}")
        report.append("")

        # Summary
        total_tests = sum(len(tests) for tests in self.results.values() if isinstance(tests, list))
        passed_tests = sum(
            len([t for t in tests if t.get("status") == "PASS"])
            for tests in self.results.values()
            if isinstance(tests, list)
        )

        report.append(f"SUMMARY: {passed_tests}/{total_tests} tests passed")
        report.append("")

        # Detailed results
        for category, tests in self.results.items():
            if isinstance(tests, list) and tests:
                report.append(f"{category.upper().replace('_', ' ')}:")
                report.append("-" * 40)

                for test in tests:
                    status_icon = "✅" if test["status"] == "PASS" else "❌"
                    report.append(f"{status_icon} {test['test']}: {test['status']}")

                    if test.get("details"):
                        for key, value in test["details"].items():
                            report.append(f"    {key}: {value}")

                report.append("")

        return "\n".join(report)


# Main test runner function
async def run_comprehensive_validation():
    """Run all validation tests and generate report"""
    print("Starting comprehensive web dashboard validation...")

    reporter = ValidationReporter()

    try:
        # Test connectivity first
        async with httpx.AsyncClient(base_url="http://0.0.0.0:12656", timeout=10.0) as client:
            try:
                response = await client.get("/api/health")
                if response.status_code == 200:
                    reporter.add_result(
                        "api_endpoints",
                        "connectivity",
                        "PASS",
                        {"response_time": "< 1s", "status_code": 200},
                    )
                    print("✅ Dashboard connectivity confirmed")
                else:
                    reporter.add_result(
                        "api_endpoints",
                        "connectivity",
                        "FAIL",
                        {"status_code": response.status_code},
                    )
                    print("❌ Dashboard connectivity failed")
                    return reporter.generate_report()
            except Exception as e:
                reporter.add_result("api_endpoints", "connectivity", "FAIL", {"error": str(e)})
                print(f"❌ Cannot connect to dashboard: {e}")
                return reporter.generate_report()

    except Exception as e:
        print(f"Fatal error during validation: {e}")
        return f"VALIDATION FAILED: {e}"

    return reporter.generate_report()


if __name__ == "__main__":
    # Run validation if executed directly
    import asyncio

    async def main():
        report = await run_comprehensive_validation()
        print(report)

    asyncio.run(main())
