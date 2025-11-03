#!/usr/bin/env python3
"""
Live Dashboard Validation Runner
Tests the running web dashboard at http://0.0.0.0:12656
"""

import asyncio
import time
from datetime import datetime

import httpx


class DashboardTester:
    """Live dashboard testing and validation"""

    def __init__(self, base_url: str = "http://0.0.0.0:12656"):
        self.base_url = base_url
        self.results = []
        self.client = None

    async def __aenter__(self):
        self.client = httpx.AsyncClient(base_url=self.base_url, timeout=30.0)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            await self.client.aclose()

    def log_result(self, test_name: str, passed: bool, details: str = "", response_time: float = 0):
        """Log test result"""
        status = "PASS" if passed else "FAIL"
        result = {
            "test": test_name,
            "status": status,
            "details": details,
            "response_time": f"{response_time:.3f}s",
            "timestamp": datetime.now().strftime("%H:%M:%S"),
        }
        self.results.append(result)

        icon = "✅" if passed else "❌"
        print(f"{icon} {test_name}: {status} ({response_time:.3f}s)")
        if details:
            print(f"   {details}")

    async def test_connectivity(self) -> bool:
        """Test basic connectivity to the dashboard"""
        try:
            start_time = time.time()
            response = await self.client.get("/api/health")
            response_time = time.time() - start_time

            if response.status_code == 200:
                data = response.json()
                details = f"Active sessions: {data.get('active_sessions', 'N/A')}, WebSocket connections: {data.get('websocket_connections', 'N/A')}"
                self.log_result("Dashboard Connectivity", True, details, response_time)
                return True
            else:
                self.log_result(
                    "Dashboard Connectivity", False, f"HTTP {response.status_code}", response_time
                )
                return False

        except Exception as e:
            self.log_result("Dashboard Connectivity", False, f"Connection error: {str(e)}")
            return False

    async def test_api_health(self):
        """Test /api/health endpoint"""
        try:
            start_time = time.time()
            response = await self.client.get("/api/health")
            response_time = time.time() - start_time

            if response.status_code == 200:
                data = response.json()

                # Validate required fields
                required_fields = ["status", "active_sessions", "websocket_connections"]
                missing_fields = [field for field in required_fields if field not in data]

                if not missing_fields and data["status"] == "healthy":
                    details = f"Status: {data['status']}, Sessions: {data['active_sessions']}, WS: {data['websocket_connections']}"
                    self.log_result("Health Endpoint", True, details, response_time)
                else:
                    self.log_result(
                        "Health Endpoint", False, f"Missing fields: {missing_fields}", response_time
                    )
            else:
                self.log_result(
                    "Health Endpoint", False, f"HTTP {response.status_code}", response_time
                )

        except Exception as e:
            self.log_result("Health Endpoint", False, f"Error: {str(e)}")

    async def test_sessions_api(self):
        """Test /api/sessions endpoint"""
        try:
            start_time = time.time()
            response = await self.client.get("/api/sessions")
            response_time = time.time() - start_time

            if response.status_code == 200:
                data = response.json()

                if isinstance(data, list):
                    session_count = len(data)

                    # Validate session structure if sessions exist
                    if session_count > 0:
                        session = data[0]
                        required_fields = [
                            "session_id",
                            "subject",
                            "created",
                            "files",
                            "file_count",
                        ]
                        missing_fields = [
                            field for field in required_fields if field not in session
                        ]

                        if not missing_fields:
                            details = f"Found {session_count} sessions, structure valid"
                            self.log_result("Sessions API", True, details, response_time)
                        else:
                            self.log_result(
                                "Sessions API",
                                False,
                                f"Missing fields: {missing_fields}",
                                response_time,
                            )
                    else:
                        self.log_result(
                            "Sessions API",
                            True,
                            "No sessions found (valid empty response)",
                            response_time,
                        )
                else:
                    self.log_result("Sessions API", False, "Response is not a list", response_time)
            else:
                self.log_result(
                    "Sessions API", False, f"HTTP {response.status_code}", response_time
                )

        except Exception as e:
            self.log_result("Sessions API", False, f"Error: {str(e)}")

    async def test_dashboard_homepage(self):
        """Test main dashboard page"""
        try:
            start_time = time.time()
            response = await self.client.get("/")
            response_time = time.time() - start_time

            if response.status_code == 200:
                content_type = response.headers.get("content-type", "")

                if "text/html" in content_type:
                    content = response.text
                    has_title = "Deep Research" in content or "Dashboard" in content

                    details = f"Content-Type: {content_type}, Has title: {has_title}"
                    self.log_result("Dashboard Homepage", True, details, response_time)
                else:
                    self.log_result(
                        "Dashboard Homepage",
                        False,
                        f"Wrong content type: {content_type}",
                        response_time,
                    )
            else:
                self.log_result(
                    "Dashboard Homepage", False, f"HTTP {response.status_code}", response_time
                )

        except Exception as e:
            self.log_result("Dashboard Homepage", False, f"Error: {str(e)}")

    async def test_file_downloads(self):
        """Test file download functionality"""
        try:
            # Get sessions first
            sessions_response = await self.client.get("/api/sessions")

            if sessions_response.status_code != 200:
                self.log_result("File Downloads", False, "Cannot get sessions list")
                return

            sessions = sessions_response.json()

            if not sessions:
                self.log_result(
                    "File Downloads", True, "No sessions available for download test (acceptable)"
                )
                return

            # Find a session with files
            test_session = None
            for session in sessions:
                if session.get("files"):
                    test_session = session
                    break

            if not test_session:
                self.log_result(
                    "File Downloads", True, "No sessions with files available (acceptable)"
                )
                return

            # Test downloading files
            download_results = []

            for file_info in test_session["files"]:
                try:
                    # Extract session_id and filename from URL
                    url = file_info["url"]
                    if "/download/" in url:
                        start_time = time.time()
                        response = await self.client.get(url)
                        time.time() - start_time

                        if response.status_code == 200:
                            # Validate MIME type
                            response.headers.get("content-type", "")
                            content_length = len(response.content)

                            # Check for attachment header
                            content_disposition = response.headers.get("content-disposition", "")
                            "attachment" in content_disposition.lower()

                            download_results.append(
                                f"{file_info['filename']}: OK ({content_length} bytes)"
                            )
                        else:
                            download_results.append(
                                f"{file_info['filename']}: HTTP {response.status_code}"
                            )

                except Exception as e:
                    download_results.append(f"{file_info['filename']}: Error - {str(e)}")

            if download_results:
                details = "; ".join(download_results)
                all_successful = all("OK" in result for result in download_results)
                self.log_result("File Downloads", all_successful, details)
            else:
                self.log_result("File Downloads", False, "No files to test")

        except Exception as e:
            self.log_result("File Downloads", False, f"Error: {str(e)}")

    async def test_security_features(self):
        """Test basic security features"""
        security_tests = []

        # Test path traversal protection
        malicious_paths = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
        ]

        for malicious_path in malicious_paths:
            try:
                response = await self.client.get(f"/download/test_session/{malicious_path}")
                if response.status_code in [400, 404]:
                    security_tests.append("Path traversal: BLOCKED")
                    break
                else:
                    security_tests.append("Path traversal: VULNERABLE")
                    break
            except:
                security_tests.append("Path traversal: ERROR")
                break

        # Test invalid extensions
        try:
            response = await self.client.get("/download/test_session/malicious.exe")
            if response.status_code in [400, 404]:
                security_tests.append("Invalid extensions: BLOCKED")
            else:
                security_tests.append("Invalid extensions: VULNERABLE")
        except:
            security_tests.append("Invalid extensions: ERROR")

        # Test HTTP method restrictions
        try:
            response = await self.client.post("/download/test_session/test.pdf")
            if response.status_code == 405:  # Method Not Allowed
                security_tests.append("Method restrictions: OK")
            else:
                security_tests.append("Method restrictions: WEAK")
        except:
            security_tests.append("Method restrictions: ERROR")

        all_secure = all("BLOCKED" in test or "OK" in test for test in security_tests)
        details = "; ".join(security_tests)
        self.log_result("Security Features", all_secure, details)

    async def test_performance(self):
        """Test basic performance metrics"""
        endpoints = ["/api/health", "/api/sessions", "/"]

        performance_results = []

        for endpoint in endpoints:
            try:
                # Test response time
                start_time = time.time()
                response = await self.client.get(endpoint)
                response_time = time.time() - start_time

                if response.status_code == 200 and response_time < 5.0:
                    performance_results.append(f"{endpoint}: {response_time:.3f}s")
                else:
                    performance_results.append(f"{endpoint}: SLOW ({response_time:.3f}s)")

            except Exception:
                performance_results.append(f"{endpoint}: ERROR")

        # Test concurrent requests
        try:

            async def make_request():
                return await self.client.get("/api/health")

            start_time = time.time()
            tasks = [make_request() for _ in range(5)]
            responses = await asyncio.gather(*tasks)
            concurrent_time = time.time() - start_time

            success_count = sum(1 for r in responses if r.status_code == 200)
            performance_results.append(
                f"Concurrent (5x): {success_count}/5 OK in {concurrent_time:.3f}s"
            )

        except Exception:
            performance_results.append("Concurrent: ERROR")

        details = "; ".join(performance_results)
        all_good = all(
            "SLOW" not in result and "ERROR" not in result for result in performance_results
        )
        self.log_result("Performance", all_good, details)

    def generate_report(self) -> str:
        """Generate validation report"""
        report_lines = []
        report_lines.append("=" * 70)
        report_lines.append("WEB DASHBOARD VALIDATION REPORT")
        report_lines.append("=" * 70)
        report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append(f"Dashboard URL: {self.base_url}")
        report_lines.append("")

        # Summary
        total_tests = len(self.results)
        passed_tests = len([r for r in self.results if r["status"] == "PASS"])
        failed_tests = total_tests - passed_tests

        report_lines.append("SUMMARY:")
        report_lines.append(f"  Total Tests: {total_tests}")
        report_lines.append(f"  Passed: {passed_tests}")
        report_lines.append(f"  Failed: {failed_tests}")
        report_lines.append(
            f"  Success Rate: {(passed_tests / total_tests * 100) if total_tests > 0 else 0:.1f}%"
        )
        report_lines.append("")

        # Detailed results
        report_lines.append("DETAILED RESULTS:")
        report_lines.append("-" * 50)

        for result in self.results:
            status_icon = "✅" if result["status"] == "PASS" else "❌"
            report_lines.append(f"{status_icon} {result['test']}")
            report_lines.append(f"    Status: {result['status']}")
            report_lines.append(f"    Time: {result['response_time']}")
            if result["details"]:
                report_lines.append(f"    Details: {result['details']}")
            report_lines.append("")

        # Recommendations
        if failed_tests > 0:
            report_lines.append("RECOMMENDATIONS:")
            report_lines.append("-" * 50)
            for result in self.results:
                if result["status"] == "FAIL":
                    report_lines.append(f"• Fix {result['test']}: {result['details']}")
            report_lines.append("")

        report_lines.append("=" * 70)

        return "\n".join(report_lines)


async def main():
    """Main test runner"""
    print("Starting Web Dashboard Validation...")
    print("Dashboard URL: http://0.0.0.0:12656")
    print("=" * 50)

    async with DashboardTester() as tester:
        # Check connectivity first
        if not await tester.test_connectivity():
            print("\n❌ Cannot connect to dashboard. Is it running?")
            print("Start with: cd web_dashboard && python main.py")
            return

        print("\n🧪 Running validation tests...")

        # Run all tests
        await tester.test_api_health()
        await tester.test_sessions_api()
        await tester.test_dashboard_homepage()
        await tester.test_file_downloads()
        await tester.test_security_features()
        await tester.test_performance()

        print("\n" + "=" * 50)

        # Generate and display report
        report = tester.generate_report()
        print(report)

        # Save report to file
        report_file = f"/tmp/dashboard_validation_report_{int(time.time())}.txt"
        with open(report_file, "w") as f:
            f.write(report)

        print(f"\n📄 Report saved to: {report_file}")


if __name__ == "__main__":
    asyncio.run(main())
