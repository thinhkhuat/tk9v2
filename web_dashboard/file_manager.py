import os
import shutil
import asyncio
import logging
import mimetypes
from pathlib import Path
from typing import List, Optional, Dict, Tuple
from datetime import datetime, timedelta
from models import FileInfo, ResearchSession

logger = logging.getLogger(__name__)

class FileManager:
    """Manages output files from CLI research and serves them for download"""
    
    def __init__(self, project_root: Path, web_static_path: Path):
        self.project_root = project_root
        self.outputs_path = project_root / "outputs"
        self.web_static_path = web_static_path
        self.downloads_path = web_static_path / "downloads"
        
        # Ensure downloads directory exists
        self.downloads_path.mkdir(parents=True, exist_ok=True)
        
        # Expected output file extensions from the actual system
        self.supported_extensions = ['.pdf', '.docx', '.md']
        
        # Note: No longer using hard-coded expected files list - using dynamic discovery
        
        # Initialize mimetypes
        mimetypes.init()
    
    def get_mime_type(self, filename: str) -> str:
        """Get MIME type for a file"""
        mime_type, _ = mimetypes.guess_type(filename)
        if mime_type:
            return mime_type
        
        # Fallback for specific file types
        ext = filename.lower().split('.')[-1]
        mime_types = {
            'pdf': 'application/pdf',
            'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'md': 'text/markdown'
        }
        return mime_types.get(ext, 'application/octet-stream')
    
    def parse_session_info(self, dir_name: str) -> Tuple[str, str]:
        """Parse session ID and subject from directory name"""
        # Format: run_{timestamp}_{subject}
        if dir_name.startswith('run_'):
            parts = dir_name.split('_', 2)
            if len(parts) >= 3:
                timestamp = parts[1]
                subject = parts[2]
                return timestamp, subject
        return dir_name, "Unknown Subject"
    
    async def get_all_research_sessions(self) -> List[ResearchSession]:
        """Get all available research sessions"""
        sessions = []
        
        if not self.outputs_path.exists():
            return sessions
        
        try:
            for dir_path in self.outputs_path.iterdir():
                if dir_path.is_dir() and dir_path.name.startswith('run_'):
                    session_id = dir_path.name
                    timestamp, subject = self.parse_session_info(session_id)
                    
                    # Get directory modification time
                    created = datetime.fromtimestamp(dir_path.stat().st_mtime)
                    
                    # Find files in this session
                    session_files = await self.discover_session_files(session_id)
                    
                    session = ResearchSession(
                        session_id=session_id,
                        subject=subject,
                        created=created,
                        files=session_files,
                        file_count=len(session_files)
                    )
                    sessions.append(session)
            
            # Sort by creation time (newest first)
            sessions.sort(key=lambda x: x.created, reverse=True)
            
        except Exception as e:
            logger.error(f"Error getting research sessions: {e}")
        
        return sessions
    
    async def discover_session_files(self, session_id: str) -> List[FileInfo]:
        """Discover actual files in a research session directory"""
        files = []
        session_dir = self.outputs_path / session_id
        
        if not session_dir.exists():
            return files
        
        try:
            # Look for files with supported extensions in the root of the session directory
            for file_path in session_dir.iterdir():
                if file_path.is_file() and file_path.suffix.lower() in self.supported_extensions:
                    # Create a more user-friendly filename based on UUID pattern and language
                    friendly_name = self.create_friendly_filename_from_uuid(file_path.name)
                    
                    file_info = FileInfo(
                        filename=friendly_name,
                        url=f"/download/{session_id}/{file_path.name}",  # Use actual filename in URL
                        size=file_path.stat().st_size,
                        created=datetime.fromtimestamp(file_path.stat().st_ctime)
                    )
                    files.append(file_info)
            
            # Sort files by type (English first, then Vietnamese) and extension
            files.sort(key=lambda f: (self.get_file_sort_priority(f.filename), f.filename))
        
        except Exception as e:
            logger.error(f"Error discovering files for session {session_id}: {e}")
        
        return files
    
    def create_friendly_filename(self, actual_filename: str, extension: str) -> str:
        """Create a user-friendly filename from the actual UUID-based filename"""
        ext = extension.lower()
        if ext == '.pdf':
            return f"research_report.pdf"
        elif ext == '.docx':
            return f"research_report.docx"
        elif ext == '.md':
            return f"research_report.md"
        else:
            return actual_filename
    
    def create_friendly_filename_from_uuid(self, uuid_filename: str) -> str:
        """Create a user-friendly filename from UUID-based filename"""
        if not uuid_filename or '.' not in uuid_filename:
            return uuid_filename
            
        # Split filename and extension
        name_part, extension = uuid_filename.rsplit('.', 1)
        extension = extension.lower()
        
        # Check if it's a translated file (ends with language code)
        if '_' in name_part and len(name_part.split('_')[-1]) <= 3:
            # This is likely a translated file (e.g., "uuid_vi.pdf")
            language_code = name_part.split('_')[-1]
            base_name = f"research_report_{language_code}"
        else:
            # This is the original file
            base_name = "research_report"
        
        return f"{base_name}.{extension}"
    
    def get_file_sort_priority(self, filename: str) -> int:
        """Get sort priority for files (lower number = higher priority)"""
        # Original files first, then translated
        if '_' in filename and not filename.startswith('research_report_'):
            return 2  # Translated files
        elif '_' in filename and filename.startswith('research_report_'):
            return 1  # Translated files with proper naming
        else:
            return 0  # Original files
    
    async def find_session_files(self, session_id: str, subject: str) -> List[FileInfo]:
        """Find output files for a completed research session"""
        files = []
        
        try:
            # Look for the most recent output directory that matches the session
            output_dirs = []
            
            if self.outputs_path.exists():
                for dir_path in self.outputs_path.iterdir():
                    if dir_path.is_dir() and dir_path.name.startswith("run_"):
                        # Check if this directory might belong to our session
                        # Based on timestamp and subject similarity
                        output_dirs.append(dir_path)
            
            # Sort by modification time (most recent first)
            output_dirs.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            # Find the most likely directory for this session
            target_dir = None
            if output_dirs:
                # For now, take the most recent directory
                # In a production system, we'd need better session tracking
                target_dir = output_dirs[0]
                logger.info(f"Found output directory for session {session_id}: {target_dir}")
            
            if target_dir and target_dir.exists():
                # Copy files to web static directory and create FileInfo objects
                session_download_dir = self.downloads_path / session_id
                session_download_dir.mkdir(exist_ok=True)
                
                # Use dynamic discovery instead of copying files
                files = await self.discover_session_files(target_dir.name)
                logger.info(f"Discovered {len(files)} files for session {session_id} in {target_dir.name}")
        
        except Exception as e:
            logger.error(f"Error finding session files for {session_id}: {e}")
        
        return files
    
    async def wait_for_files(self, session_id: str, subject: str, timeout: int = 300) -> List[FileInfo]:
        """Wait for output files to be generated, with timeout"""
        start_time = datetime.now()
        
        while (datetime.now() - start_time).seconds < timeout:
            # Use the new dynamic discovery method
            files = await self.discover_session_files(session_id)
            
            if files:
                logger.info(f"Found {len(files)} files for session {session_id}")
                return files
            
            # Wait a bit before checking again
            await asyncio.sleep(2)
        
        logger.warning(f"Timeout waiting for files for session {session_id}")
        return []
    
    async def cleanup_old_files(self, max_age_hours: int = 24) -> int:
        """Clean up old downloaded files"""
        cleaned_count = 0
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        
        try:
            if self.downloads_path.exists():
                for session_dir in self.downloads_path.iterdir():
                    if session_dir.is_dir():
                        # Check if directory is old enough to clean
                        dir_mtime = datetime.fromtimestamp(session_dir.stat().st_mtime)
                        
                        if dir_mtime < cutoff_time:
                            # Remove the entire session directory
                            shutil.rmtree(session_dir)
                            cleaned_count += 1
                            logger.info(f"Cleaned up old session directory: {session_dir.name}")
        
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
        
        return cleaned_count
    
    def get_file_path(self, session_id: str, filename: str) -> Optional[Path]:
        """Get the full path to a downloadable file"""
        # First try the downloads directory (for legacy compatibility)
        file_path = self.downloads_path / session_id / filename
        if file_path.exists() and file_path.is_file():
            return file_path
        
        # Try the actual outputs directory (new approach)
        session_dir = self.outputs_path / session_id
        if session_dir.exists():
            # Look for the file by actual filename (UUID-based)
            for file_path in session_dir.iterdir():
                if file_path.is_file() and file_path.name == filename:
                    return file_path
        
        return None
    
    def is_valid_filename(self, filename: str) -> bool:
        """Check if filename has a supported extension"""
        if not filename or '.' not in filename:
            return False
        
        extension = '.' + filename.split('.')[-1].lower()
        return extension in self.supported_extensions
    
    async def get_session_files(self, session_id: str) -> List[FileInfo]:
        """Get list of available files for a session"""
        # Use the new discovery method
        return await self.discover_session_files(session_id)