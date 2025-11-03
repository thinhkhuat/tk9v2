import asyncio
import logging
import mimetypes
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Tuple

from .filename_utils import FilenameParser, build_download_url
from .models import FileInfo, ResearchSession

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
        # DRY: Use single source of truth from FilenameParser
        self.supported_extensions = set(FilenameParser.SUPPORTED_EXTENSIONS)

        # Note: No longer using hard-coded expected files list - using dynamic discovery

        # Initialize mimetypes
        mimetypes.init()

    def get_mime_type(self, filename: str) -> str:
        """Get MIME type for a file - delegates to centralized FilenameParser"""
        # MIGRATED: Use centralized module instead of duplicate logic
        return FilenameParser.get_mime_type(filename)

    def parse_session_info(self, dir_name: str) -> Tuple[str, str]:
        """Parse session ID and subject from directory name"""
        # Format: run_{timestamp}_{subject}
        if dir_name.startswith("run_"):
            parts = dir_name.split("_", 2)
            if len(parts) >= 3:
                timestamp = parts[1]
                subject = parts[2]
                return timestamp, subject
        return dir_name, "Unknown Subject"

    async def get_all_research_sessions(self) -> List[ResearchSession]:
        """
        Get all available research sessions.

        DEPRECATED: This method is for filesystem-only mode.
        For database-backed sessions, use database.get_user_sessions() instead.

        DRY VIOLATION WARNING: This calculates file_count on-the-fly.
        Use database columns for production.
        """
        sessions: List[ResearchSession] = []

        if not self.outputs_path.exists():
            return sessions

        try:
            for dir_path in self.outputs_path.iterdir():
                if dir_path.is_dir() and dir_path.name.startswith("run_"):
                    session_id = dir_path.name
                    timestamp, subject = self.parse_session_info(session_id)

                    # Get directory modification time
                    created = datetime.fromtimestamp(dir_path.stat().st_mtime)

                    # Find files in this session
                    session_files = await self.discover_session_files(session_id)

                    # DEPRECATED: Calculating file_count on-the-fly violates DRY
                    # TODO: Remove this method once all sessions use database
                    session = ResearchSession(
                        session_id=session_id,
                        subject=subject,
                        created=created,
                        files=session_files,
                        file_count=len(session_files),  # DEPRECATED - use DB instead
                    )
                    sessions.append(session)

            # Sort by creation time (newest first)
            sessions.sort(key=lambda x: x.created, reverse=True)

        except Exception as e:
            logger.error(f"Error getting research sessions: {e}")

        return sessions

    async def discover_session_files(self, session_id: str) -> List[FileInfo]:
        """Discover actual files in a research session directory"""
        files: List[FileInfo] = []
        session_dir = self.outputs_path / session_id

        if not session_dir.exists():
            return files

        try:
            # Look for files with supported extensions in the root of the session directory
            for file_path in session_dir.iterdir():
                if file_path.is_file() and file_path.suffix.lower() in self.supported_extensions:
                    # DRY: Use centralized FilenameParser to extract ALL file metadata
                    parsed_file = FilenameParser.parse(file_path.name)

                    if parsed_file:
                        # Use actual filename (UUID or otherwise) for uniqueness
                        file_info = FileInfo(
                            filename=file_path.name,
                            url=build_download_url(session_id, file_path.name),
                            size=file_path.stat().st_size,
                            created=datetime.fromtimestamp(file_path.stat().st_ctime),
                            file_type=parsed_file.file_type.value,
                            language=parsed_file.language.value,
                            friendly_name=parsed_file.friendly_name,
                        )
                        files.append(file_info)
                    else:
                        # Fallback path: accept non-UUID filenames with supported extensions
                        # Extract best-effort metadata so UI still renders files
                        fallback_type = FilenameParser.extract_file_type(file_path.name)
                        fallback_lang = FilenameParser.extract_language(file_path.name)
                        friendly = FilenameParser.to_friendly_name(file_path.name)

                        file_info = FileInfo(
                            filename=file_path.name,
                            url=build_download_url(session_id, file_path.name),
                            size=file_path.stat().st_size,
                            created=datetime.fromtimestamp(file_path.stat().st_ctime),
                            file_type=fallback_type.value,
                            language=fallback_lang.value,
                            friendly_name=friendly,
                        )
                        files.append(file_info)

            # Sort files by type (English first, then Vietnamese) and extension
            files.sort(key=lambda f: (self.get_file_sort_priority(f.filename), f.filename))

        except Exception as e:
            logger.error(f"Error discovering files for session {session_id}: {e}")

        return files

    def create_friendly_filename_from_uuid(self, uuid_filename: str) -> str:
        """Create a user-friendly filename from UUID-based filename - delegates to centralized FilenameParser"""
        # MIGRATED: Use centralized module instead of duplicate logic
        # DELETED: create_friendly_filename() - inferior version removed
        return FilenameParser.to_friendly_name(uuid_filename)

    def get_file_sort_priority(self, filename: str) -> int:
        """Get sort priority for files - delegates to centralized FilenameParser"""
        # MIGRATED: Use centralized module instead of duplicate logic
        return FilenameParser.get_sort_priority(filename)

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
                logger.info(
                    f"Discovered {len(files)} files for session {session_id} in {target_dir.name}"
                )

        except Exception as e:
            logger.error(f"Error finding session files for {session_id}: {e}")

        return files

    async def wait_for_files(
        self, session_id: str, subject: str, timeout: int = 300
    ) -> List[FileInfo]:
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
        """Check if filename has a supported extension - delegates to centralized FilenameParser"""
        # MIGRATED: Use centralized module instead of duplicate logic
        return FilenameParser.is_valid(filename)

    async def get_session_files(self, session_id: str) -> List[FileInfo]:
        """Get list of available files for a session"""
        # Use the new discovery method
        return await self.discover_session_files(session_id)
