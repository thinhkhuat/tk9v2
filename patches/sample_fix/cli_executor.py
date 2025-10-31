import asyncio
import os
import subprocess
import logging
from pathlib import Path
from typing import AsyncGenerator, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class CLIExecutor:
    """Handles execution of the CLI command and streaming of logs"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.sessions = {}  # Track running sessions
        
    async def execute_research(self, subject: str, language: str, session_id: str) -> AsyncGenerator[str, None]:
        """
        Execute the CLI research command and stream logs
        
        Command: uv run python -m main -r "SUBJECT" -l vi --save-files
        """
        try:
            # Sanitize the subject input
            sanitized_subject = self._sanitize_input(subject)
            
            # Build the command
            cmd = [
                "uv", "run", "python", "-m", "main", 
                "-r", sanitized_subject,
                "-l", language,
                "--save-files",
                "--verbose"  # Ensure verbose output
            ]
            
            logger.info(f"Starting research for session {session_id}: {sanitized_subject}")
            
            # Start the process
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                cwd=self.project_root
            )
            
            # Store process reference
            self.sessions[session_id] = {
                'process': process,
                'status': 'running',
                'start_time': datetime.now(),
                'subject': sanitized_subject
            }
            
            # Stream output
            yield f"[SYSTEM] Starting research: {sanitized_subject}\n"
            yield f"[SYSTEM] Command: {' '.join(cmd)}\n"
            yield f"[SYSTEM] Session ID: {session_id}\n"
            yield "=" * 80 + "\n"
            
            # Read and yield output line by line
            while True:
                line = await process.stdout.readline()
                if not line:
                    break
                    
                decoded_line = line.decode('utf-8', errors='replace')
                yield decoded_line
                
                # Log significant actual errors (not informational messages about error handling)
                # Skip lines that are just describing error handling features
                lower_line = decoded_line.lower()
                if ("error" in lower_line or "exception" in lower_line) and \
                   not ("error catching" in lower_line or 
                        "error handling" in lower_line or 
                        "graceful degradation" in lower_line or
                        "text processing fixes applied" in lower_line):
                    logger.warning(f"Error in session {session_id}: {decoded_line.strip()}")
                    
            # Wait for process to complete
            return_code = await process.wait()
            
            # Update session status
            self.sessions[session_id]['status'] = 'completed' if return_code == 0 else 'failed'
            self.sessions[session_id]['return_code'] = return_code
            self.sessions[session_id]['end_time'] = datetime.now()
            
            if return_code == 0:
                yield f"\n[SYSTEM] Research completed successfully!\n"
                yield f"[SYSTEM] Output files should be available in ./outputs/\n"
                logger.info(f"Session {session_id} completed successfully")
            else:
                yield f"\n[SYSTEM] Research failed with return code: {return_code}\n"
                logger.error(f"Session {session_id} failed with return code: {return_code}")
                
        except Exception as e:
            error_msg = f"Error executing research: {str(e)}"
            logger.error(f"Session {session_id} error: {error_msg}")
            
            if session_id in self.sessions:
                self.sessions[session_id]['status'] = 'failed'
                self.sessions[session_id]['error'] = str(e)
                
            yield f"\n[SYSTEM ERROR] {error_msg}\n"
    
    def _sanitize_input(self, subject: str) -> str:
        """Sanitize user input to prevent command injection"""
        # Remove potentially dangerous characters
        dangerous_chars = ['`', '$', '&', '|', ';', '>', '<', '(', ')', '{', '}']
        sanitized = subject
        
        for char in dangerous_chars:
            sanitized = sanitized.replace(char, '')
            
        # Limit length
        sanitized = sanitized[:1000]
        
        # Ensure it's not empty after sanitization
        if not sanitized.strip():
            sanitized = "general research topic"
            
        return sanitized.strip()
    
    def get_session_status(self, session_id: str) -> Optional[dict]:
        """Get the current status of a session"""
        return self.sessions.get(session_id)
    
    def cleanup_session(self, session_id: str) -> bool:
        """Clean up a completed session"""
        if session_id in self.sessions:
            session = self.sessions[session_id]
            if session.get('process') and session['process'].returncode is None:
                # Process is still running
                return False
            
            # Remove from tracking
            del self.sessions[session_id]
            logger.info(f"Cleaned up session {session_id}")
            return True
        return False
    
    async def stop_session(self, session_id: str) -> bool:
        """Stop a running session"""
        if session_id in self.sessions:
            session = self.sessions[session_id]
            process = session.get('process')
            
            if process and process.returncode is None:
                try:
                    process.terminate()
                    await asyncio.wait_for(process.wait(), timeout=10)
                    logger.info(f"Stopped session {session_id}")
                    return True
                except asyncio.TimeoutError:
                    process.kill()
                    await process.wait()
                    logger.warning(f"Force killed session {session_id}")
                    return True
                except Exception as e:
                    logger.error(f"Error stopping session {session_id}: {e}")
                    return False
        return False