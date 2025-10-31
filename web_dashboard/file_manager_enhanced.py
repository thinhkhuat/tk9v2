import os
import shutil
import asyncio
import logging
import mimetypes
import zipfile
import tempfile
from pathlib import Path
from typing import List, Optional, Dict, Tuple
from datetime import datetime, timedelta
from models import FileInfo, ResearchSession
import hashlib
import json

logger = logging.getLogger(__name__)

class EnhancedFileManager:
    """Enhanced file manager with additional download capabilities"""

    def __init__(self, project_root: Path, web_static_path: Path):
        self.project_root = project_root
        self.outputs_path = project_root / "outputs"
        self.web_static_path = web_static_path
        self.downloads_path = web_static_path / "downloads"
        self.temp_path = web_static_path / "temp"

        # Ensure directories exist
        self.downloads_path.mkdir(parents=True, exist_ok=True)
        self.temp_path.mkdir(parents=True, exist_ok=True)

        # Expected output file extensions from the actual system
        self.supported_extensions = ['.pdf', '.docx', '.md', '.txt', '.json']

        # Preview support
        self.preview_extensions = ['.md', '.txt', '.json']

        # Initialize mimetypes
        mimetypes.init()

        # Download history cache
        self.download_history = []
        self.max_history = 100

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
            'md': 'text/markdown',
            'txt': 'text/plain',
            'json': 'application/json',
            'zip': 'application/zip'
        }
        return mime_types.get(ext, 'application/octet-stream')

    async def create_session_zip(self, session_id: str) -> Optional[Path]:
        """Create a ZIP file containing all files from a session"""
        try:
            session_dir = self.outputs_path / session_id
            if not session_dir.exists():
                logger.error(f"Session directory not found: {session_dir}")
                return None

            # Create temporary ZIP file
            zip_filename = f"{session_id}_all_files.zip"
            zip_path = self.temp_path / zip_filename

            # Check if ZIP already exists and is recent (cache for 1 hour)
            if zip_path.exists():
                file_age = datetime.now() - datetime.fromtimestamp(zip_path.stat().st_mtime)
                if file_age < timedelta(hours=1):
                    logger.info(f"Using cached ZIP file: {zip_path}")
                    return zip_path

            # Create new ZIP file
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                files_added = 0

                # Add all supported files from the session directory
                for file_path in session_dir.iterdir():
                    if file_path.is_file() and file_path.suffix.lower() in self.supported_extensions:
                        # Create user-friendly name in ZIP
                        friendly_name = self.create_friendly_filename_from_uuid(file_path.name)
                        zipf.write(file_path, arcname=friendly_name)
                        files_added += 1
                        logger.info(f"Added to ZIP: {friendly_name}")

                # Add drafts if they exist
                drafts_dir = session_dir / "drafts"
                if drafts_dir.exists():
                    for file_path in drafts_dir.rglob("*"):
                        if file_path.is_file() and file_path.suffix.lower() in self.supported_extensions:
                            relative_path = file_path.relative_to(session_dir)
                            zipf.write(file_path, arcname=str(relative_path))
                            files_added += 1

            if files_added == 0:
                logger.warning(f"No files found to add to ZIP for session {session_id}")
                zip_path.unlink()  # Remove empty ZIP
                return None

            logger.info(f"Created ZIP with {files_added} files: {zip_path}")
            return zip_path

        except Exception as e:
            logger.error(f"Error creating ZIP for session {session_id}: {e}")
            return None

    async def get_file_preview(self, session_id: str, filename: str, max_lines: int = 50) -> Optional[Dict]:
        """Get a preview of a text-based file"""
        try:
            file_path = self.get_file_path(session_id, filename)
            if not file_path:
                return None

            # Check if file is previewable
            if file_path.suffix.lower() not in self.preview_extensions:
                return {"error": "File type not previewable", "supported": False}

            # Read file content
            content_lines = []
            total_lines = 0
            file_size = file_path.stat().st_size

            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line_num, line in enumerate(f, 1):
                    if line_num <= max_lines:
                        content_lines.append(line.rstrip())
                    total_lines = line_num

            preview_data = {
                "supported": True,
                "filename": filename,
                "content": "\n".join(content_lines),
                "total_lines": total_lines,
                "preview_lines": len(content_lines),
                "truncated": total_lines > max_lines,
                "file_size": file_size,
                "mime_type": self.get_mime_type(filename)
            }

            return preview_data

        except Exception as e:
            logger.error(f"Error getting preview for {filename}: {e}")
            return {"error": str(e), "supported": False}

    async def get_session_statistics(self, session_id: str) -> Dict:
        """Get statistics about a research session"""
        try:
            session_dir = self.outputs_path / session_id
            if not session_dir.exists():
                return {}

            stats = {
                "total_files": 0,
                "total_size": 0,
                "file_types": {},
                "languages": set(),
                "creation_date": None,
                "last_modified": None
            }

            # Analyze files
            for file_path in session_dir.iterdir():
                if file_path.is_file() and file_path.suffix.lower() in self.supported_extensions:
                    stats["total_files"] += 1
                    file_size = file_path.stat().st_size
                    stats["total_size"] += file_size

                    # Track file types
                    ext = file_path.suffix.lower()
                    stats["file_types"][ext] = stats["file_types"].get(ext, 0) + 1

                    # Detect language from filename
                    if '_vi' in file_path.name:
                        stats["languages"].add("Vietnamese")
                    elif '_en' in file_path.name:
                        stats["languages"].add("English")
                    else:
                        stats["languages"].add("Original")

                    # Track dates
                    file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if not stats["creation_date"] or file_mtime < stats["creation_date"]:
                        stats["creation_date"] = file_mtime
                    if not stats["last_modified"] or file_mtime > stats["last_modified"]:
                        stats["last_modified"] = file_mtime

            # Convert set to list for JSON serialization
            stats["languages"] = list(stats["languages"])

            # Format dates
            if stats["creation_date"]:
                stats["creation_date"] = stats["creation_date"].isoformat()
            if stats["last_modified"]:
                stats["last_modified"] = stats["last_modified"].isoformat()

            return stats

        except Exception as e:
            logger.error(f"Error getting session statistics: {e}")
            return {}

    async def search_files(self, query: str, session_id: Optional[str] = None) -> List[Dict]:
        """Search for files across sessions or within a specific session"""
        results = []
        query_lower = query.lower()

        try:
            if session_id:
                # Search within specific session
                sessions = [session_id]
            else:
                # Search all sessions
                sessions = [d.name for d in self.outputs_path.iterdir() if d.is_dir()]

            for sess_id in sessions:
                session_dir = self.outputs_path / sess_id
                if not session_dir.exists():
                    continue

                # Parse session info
                timestamp, subject = self.parse_session_info(sess_id)

                # Check if subject matches query
                if query_lower in subject.lower():
                    # Add all files from matching session
                    files = await self.discover_session_files(sess_id)
                    for file in files:
                        results.append({
                            "session_id": sess_id,
                            "session_subject": subject,
                            "file": file.dict(),
                            "match_type": "session_subject"
                        })

                # Check individual files
                for file_path in session_dir.iterdir():
                    if file_path.is_file() and file_path.suffix.lower() in self.supported_extensions:
                        friendly_name = self.create_friendly_filename_from_uuid(file_path.name)

                        if query_lower in friendly_name.lower():
                            file_info = FileInfo(
                                filename=friendly_name,
                                url=f"/download/{sess_id}/{file_path.name}",
                                size=file_path.stat().st_size,
                                created=datetime.fromtimestamp(file_path.stat().st_ctime)
                            )

                            results.append({
                                "session_id": sess_id,
                                "session_subject": subject,
                                "file": file_info.dict(),
                                "match_type": "filename"
                            })

            return results

        except Exception as e:
            logger.error(f"Error searching files: {e}")
            return []

    def track_download(self, session_id: str, filename: str, user_info: Optional[Dict] = None):
        """Track file download for analytics"""
        download_record = {
            "timestamp": datetime.now().isoformat(),
            "session_id": session_id,
            "filename": filename,
            "user_info": user_info or {}
        }

        self.download_history.append(download_record)

        # Limit history size
        if len(self.download_history) > self.max_history:
            self.download_history = self.download_history[-self.max_history:]

        # Optionally save to file for persistence
        try:
            history_file = self.downloads_path / "download_history.json"
            with open(history_file, 'w') as f:
                json.dump(self.download_history, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving download history: {e}")

    async def get_download_history(self, limit: int = 10) -> List[Dict]:
        """Get recent download history"""
        return self.download_history[-limit:]

    async def cleanup_temp_files(self, max_age_hours: int = 2):
        """Clean up old temporary files"""
        cleaned_count = 0
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)

        try:
            if self.temp_path.exists():
                for file_path in self.temp_path.iterdir():
                    if file_path.is_file():
                        file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                        if file_mtime < cutoff_time:
                            file_path.unlink()
                            cleaned_count += 1
                            logger.info(f"Cleaned up temp file: {file_path.name}")

        except Exception as e:
            logger.error(f"Error cleaning temp files: {e}")

        return cleaned_count

    def calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of a file"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    async def get_file_metadata(self, session_id: str, filename: str) -> Optional[Dict]:
        """Get detailed metadata for a file"""
        try:
            file_path = self.get_file_path(session_id, filename)
            if not file_path:
                return None

            stat = file_path.stat()

            metadata = {
                "filename": filename,
                "friendly_name": self.create_friendly_filename_from_uuid(filename),
                "size": stat.st_size,
                "size_formatted": self.format_file_size(stat.st_size),
                "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "mime_type": self.get_mime_type(filename),
                "extension": file_path.suffix.lower(),
                "hash": self.calculate_file_hash(file_path),
                "previewable": file_path.suffix.lower() in self.preview_extensions
            }

            return metadata

        except Exception as e:
            logger.error(f"Error getting file metadata: {e}")
            return None

    def format_file_size(self, bytes: int) -> str:
        """Format file size in human-readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes < 1024.0:
                return f"{bytes:.2f} {unit}"
            bytes /= 1024.0
        return f"{bytes:.2f} TB"

    # Include all original methods from FileManager
    def parse_session_info(self, dir_name: str) -> Tuple[str, str]:
        """Parse session ID and subject from directory name"""
        if dir_name.startswith('run_'):
            parts = dir_name.split('_', 2)
            if len(parts) >= 3:
                timestamp = parts[1]
                subject = parts[2]
                return timestamp, subject
        return dir_name, "Unknown Subject"

    def create_friendly_filename_from_uuid(self, uuid_filename: str) -> str:
        """Create a user-friendly filename from UUID-based filename"""
        if not uuid_filename or '.' not in uuid_filename:
            return uuid_filename

        name_part, extension = uuid_filename.rsplit('.', 1)
        extension = extension.lower()

        if '_' in name_part and len(name_part.split('_')[-1]) <= 3:
            language_code = name_part.split('_')[-1]
            base_name = f"research_report_{language_code}"
        else:
            base_name = "research_report"

        return f"{base_name}.{extension}"

    async def discover_session_files(self, session_id: str) -> List[FileInfo]:
        """Discover actual files in a research session directory"""
        files = []
        session_dir = self.outputs_path / session_id

        if not session_dir.exists():
            return files

        try:
            for file_path in session_dir.iterdir():
                if file_path.is_file() and file_path.suffix.lower() in self.supported_extensions:
                    friendly_name = self.create_friendly_filename_from_uuid(file_path.name)

                    file_info = FileInfo(
                        filename=friendly_name,
                        url=f"/download/{session_id}/{file_path.name}",
                        size=file_path.stat().st_size,
                        created=datetime.fromtimestamp(file_path.stat().st_ctime)
                    )
                    files.append(file_info)

            files.sort(key=lambda f: (self.get_file_sort_priority(f.filename), f.filename))

        except Exception as e:
            logger.error(f"Error discovering files for session {session_id}: {e}")

        return files

    def get_file_sort_priority(self, filename: str) -> int:
        """Get sort priority for files"""
        if '_' in filename and filename.startswith('research_report_'):
            return 1
        elif '_' not in filename:
            return 0
        else:
            return 2

    def get_file_path(self, session_id: str, filename: str) -> Optional[Path]:
        """Get the full path to a downloadable file"""
        file_path = self.downloads_path / session_id / filename
        if file_path.exists() and file_path.is_file():
            return file_path

        session_dir = self.outputs_path / session_id
        if session_dir.exists():
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
        return await self.discover_session_files(session_id)

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

                    created = datetime.fromtimestamp(dir_path.stat().st_mtime)
                    session_files = await self.discover_session_files(session_id)

                    session = ResearchSession(
                        session_id=session_id,
                        subject=subject,
                        created=created,
                        files=session_files,
                        file_count=len(session_files)
                    )
                    sessions.append(session)

            sessions.sort(key=lambda x: x.created, reverse=True)

        except Exception as e:
            logger.error(f"Error getting research sessions: {e}")

        return sessions