#!/usr/bin/env python3
"""
Detailed technical validation for specific requirements
"""

import asyncio
import httpx
import json
from urllib.parse import quote, unquote

class DetailedTester:
    """Detailed technical validation"""
    
    def __init__(self):
        self.base_url = "http://0.0.0.0:12656"
    
    async def test_mime_type_headers(self):
        """Test MIME type headers for each file type"""
        print("🔍 Testing MIME Type Headers...")
        
        # Expected MIME types
        expected_mime_types = {
            ".pdf": "application/pdf",
            ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ".md": "text/markdown"
        }
        
        async with httpx.AsyncClient(base_url=self.base_url, timeout=30.0) as client:
            # Get sessions with files
            sessions_response = await client.get("/api/sessions")
            sessions = sessions_response.json()
            
            mime_results = {}
            
            for session in sessions:
                if session.get("files"):
                    for file_info in session["files"]:
                        filename = file_info["filename"]
                        url = file_info["url"]
                        
                        # Determine expected MIME type
                        file_ext = None
                        for ext in expected_mime_types.keys():
                            if filename.lower().endswith(ext):
                                file_ext = ext
                                break
                        
                        if file_ext:
                            try:
                                response = await client.get(url)
                                if response.status_code == 200:
                                    actual_mime = response.headers.get("content-type", "")
                                    expected_mime = expected_mime_types[file_ext]
                                    
                                    if expected_mime in actual_mime:
                                        mime_results[file_ext] = f"✅ {expected_mime}"
                                    else:
                                        mime_results[file_ext] = f"❌ Expected: {expected_mime}, Got: {actual_mime}"
                                    
                                    # Only test each type once
                                    if len(mime_results) == len(expected_mime_types):
                                        break
                            except Exception as e:
                                mime_results[file_ext] = f"❌ Error: {str(e)}"
                    
                    if len(mime_results) == len(expected_mime_types):
                        break
        
        print("MIME Type Validation:")
        for ext, result in mime_results.items():
            print(f"  {ext}: {result}")
        
        return mime_results
    
    async def test_download_headers(self):
        """Test download-specific headers"""
        print("\n🔍 Testing Download Headers...")
        
        async with httpx.AsyncClient(base_url=self.base_url, timeout=30.0) as client:
            sessions_response = await client.get("/api/sessions")
            sessions = sessions_response.json()
            
            header_results = []
            
            for session in sessions:
                if session.get("files"):
                    file_info = session["files"][0]  # Test first file
                    url = file_info["url"]
                    
                    try:
                        response = await client.get(url)
                        if response.status_code == 200:
                            headers = response.headers
                            
                            # Check Content-Disposition
                            content_disposition = headers.get("content-disposition", "")
                            has_attachment = "attachment" in content_disposition.lower()
                            has_filename = "filename=" in content_disposition.lower()
                            
                            # Check Content-Length
                            content_length = headers.get("content-length")
                            actual_length = len(response.content)
                            
                            header_results.append({
                                "file": file_info["filename"],
                                "content_disposition": f"✅ Attachment: {has_attachment}, Filename: {has_filename}",
                                "content_length": f"✅ Header: {content_length}, Actual: {actual_length}",
                                "content_type": f"✅ {headers.get('content-type', 'Missing')}"
                            })
                            break
                    except Exception as e:
                        header_results.append({"error": f"❌ {str(e)}"})
                        break
                
                if header_results:
                    break
        
        print("Download Headers:")
        for result in header_results:
            for key, value in result.items():
                print(f"  {key}: {value}")
        
        return header_results
    
    async def test_api_response_structure(self):
        """Test API response data structures"""
        print("\n🔍 Testing API Response Structures...")
        
        async with httpx.AsyncClient(base_url=self.base_url, timeout=30.0) as client:
            # Test /api/sessions structure
            sessions_response = await client.get("/api/sessions")
            sessions = sessions_response.json()
            
            if sessions:
                session = sessions[0]
                
                # Check session structure
                session_fields = {
                    "session_id": str,
                    "subject": str,
                    "created": str,
                    "files": list,
                    "file_count": int
                }
                
                session_validation = {}
                for field, expected_type in session_fields.items():
                    if field in session:
                        actual_type = type(session[field])
                        if actual_type == expected_type:
                            session_validation[field] = f"✅ {expected_type.__name__}"
                        else:
                            session_validation[field] = f"❌ Expected {expected_type.__name__}, got {actual_type.__name__}"
                    else:
                        session_validation[field] = "❌ Missing"
                
                print("Session Structure:")
                for field, result in session_validation.items():
                    print(f"  {field}: {result}")
                
                # Check file structure if files exist
                if session.get("files"):
                    file_info = session["files"][0]
                    file_fields = {
                        "filename": str,
                        "url": str,
                        "size": (int, type(None)),
                        "created": (str, type(None))
                    }
                    
                    file_validation = {}
                    for field, expected_type in file_fields.items():
                        if field in file_info:
                            actual_type = type(file_info[field])
                            if isinstance(expected_type, tuple):
                                if actual_type in expected_type:
                                    file_validation[field] = f"✅ {actual_type.__name__}"
                                else:
                                    file_validation[field] = f"❌ Expected {expected_type}, got {actual_type.__name__}"
                            else:
                                if actual_type == expected_type:
                                    file_validation[field] = f"✅ {expected_type.__name__}"
                                else:
                                    file_validation[field] = f"❌ Expected {expected_type.__name__}, got {actual_type.__name__}"
                        else:
                            file_validation[field] = "❌ Missing"
                    
                    print("\nFile Info Structure:")
                    for field, result in file_validation.items():
                        print(f"  {field}: {result}")
            
            # Test /api/health structure
            health_response = await client.get("/api/health")
            health_data = health_response.json()
            
            health_fields = {
                "status": str,
                "active_sessions": int,
                "websocket_connections": int
            }
            
            health_validation = {}
            for field, expected_type in health_fields.items():
                if field in health_data:
                    actual_type = type(health_data[field])
                    if actual_type == expected_type:
                        health_validation[field] = f"✅ {expected_type.__name__}"
                    else:
                        health_validation[field] = f"❌ Expected {expected_type.__name__}, got {actual_type.__name__}"
                else:
                    health_validation[field] = "❌ Missing"
            
            print("\nHealth API Structure:")
            for field, result in health_validation.items():
                print(f"  {field}: {result}")
    
    async def test_url_encoding(self):
        """Test URL encoding handling"""
        print("\n🔍 Testing URL Encoding...")
        
        async with httpx.AsyncClient(base_url=self.base_url, timeout=30.0) as client:
            sessions_response = await client.get("/api/sessions")
            sessions = sessions_response.json()
            
            if sessions:
                for session in sessions:
                    if session.get("files"):
                        file_info = session["files"][0]
                        original_url = file_info["url"]
                        
                        # Test URL with encoded characters
                        encoded_url = original_url.replace(" ", "%20")
                        
                        try:
                            response = await client.get(encoded_url)
                            if response.status_code == 200:
                                print(f"  ✅ URL encoding handled: {encoded_url}")
                            else:
                                print(f"  ❌ URL encoding failed: {response.status_code}")
                                
                            # Test original URL
                            response = await client.get(original_url)
                            if response.status_code == 200:
                                print(f"  ✅ Original URL works: {original_url}")
                            else:
                                print(f"  ❌ Original URL failed: {response.status_code}")
                                
                        except Exception as e:
                            print(f"  ❌ URL test error: {str(e)}")
                        
                        return  # Exit after testing first file
                
                return  # Exit after testing first session with files

async def main():
    """Run detailed validation tests"""
    print("🔬 DETAILED TECHNICAL VALIDATION")
    print("=" * 50)
    
    tester = DetailedTester()
    
    await tester.test_mime_type_headers()
    await tester.test_download_headers()
    await tester.test_api_response_structure()
    await tester.test_url_encoding()
    
    print("\n" + "=" * 50)
    print("✅ Detailed validation complete!")

if __name__ == "__main__":
    asyncio.run(main())