#!/usr/bin/env python
"""
Direct Timeout Patch for GPT-Researcher
Directly modifies the source files to fix the 4-second timeout issue

This is a more aggressive approach that directly patches the installed gpt-researcher files
"""

import os
import re
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class DirectTimeoutPatcher:
    """Directly patch the gpt-researcher source files"""
    
    def __init__(self):
        self.gpt_researcher_path = None
        self.backup_suffix = '.timeout_patch_backup'
        
    def find_gpt_researcher_path(self):
        """Find the installed gpt-researcher package path"""
        try:
            import gpt_researcher
            self.gpt_researcher_path = Path(gpt_researcher.__file__).parent
            logger.info(f"Found gpt-researcher at: {self.gpt_researcher_path}")
            return True
        except ImportError:
            logger.error("Could not find gpt-researcher package")
            return False
    
    def backup_file(self, file_path):
        """Create a backup of the original file"""
        backup_path = Path(str(file_path) + self.backup_suffix)
        if not backup_path.exists():
            try:
                backup_path.write_text(file_path.read_text())
                logger.info(f"Created backup: {backup_path}")
                return True
            except Exception as e:
                logger.error(f"Failed to create backup of {file_path}: {e}")
                return False
        else:
            logger.info(f"Backup already exists: {backup_path}")
            return True
    
    def patch_timeout_in_file(self, file_path, old_timeout=4, new_timeout=30):
        """Patch timeout values in a specific file"""
        try:
            content = file_path.read_text()
            
            # Pattern to match timeout=4 in various contexts
            patterns = [
                (rf'timeout={old_timeout}\b', f'timeout={new_timeout}'),
                (rf'timeout\s*=\s*{old_timeout}\b', f'timeout={new_timeout}'),
            ]
            
            original_content = content
            changes_made = 0
            
            for pattern, replacement in patterns:
                new_content = re.sub(pattern, replacement, content)
                if new_content != content:
                    changes_made += len(re.findall(pattern, content))
                    content = new_content
            
            if changes_made > 0:
                # Create backup first
                if self.backup_file(file_path):
                    file_path.write_text(content)
                    logger.info(f"✅ Patched {file_path}: {changes_made} timeout changes made")
                    return True
                else:
                    logger.error(f"❌ Could not backup {file_path}, skipping patch")
                    return False
            else:
                logger.info(f"ℹ️  No timeout={old_timeout} found in {file_path}")
                return True
                
        except Exception as e:
            logger.error(f"❌ Failed to patch {file_path}: {e}")
            return False
    
    def add_retry_logic_to_file(self, file_path):
        """Add retry logic and better error handling to scraper files"""
        try:
            content = file_path.read_text()
            
            # Check if already patched
            if 'timeout_patch_retry_logic' in content:
                logger.info(f"ℹ️  {file_path} already has retry logic")
                return True
            
            # Add imports at the top
            import_additions = '''
# Network reliability patch imports
import time
import random
from requests.adapters import HTTPAdapter
try:
    from requests.packages.urllib3.util.retry import Retry
except ImportError:
    from urllib3.util.retry import Retry
# timeout_patch_retry_logic marker
'''

            # Find where to insert imports (after existing imports)
            if 'timeout_patch_retry_logic' not in content:
                if 'import requests' in content:
                    content = content.replace('import requests', f'import requests{import_additions}')
                elif 'from requests' in content:
                    # Find the first 'from requests' import
                    lines = content.split('\n')
                    for i, line in enumerate(lines):
                        if line.strip().startswith('from requests'):
                            lines.insert(i + 1, import_additions)
                            content = '\n'.join(lines)
                            break
                else:
                    # If no requests import found, add after first import statement
                    lines = content.split('\n')
                    for i, line in enumerate(lines):
                        if line.strip().startswith('import ') or line.strip().startswith('from '):
                            lines.insert(i + 1, import_additions)
                            content = '\n'.join(lines)
                            break
            
            # Enhanced session configuration
            session_enhancement = '''
        # Network reliability enhancement
        if hasattr(self, 'session') and self.session:
            retry_strategy = Retry(
                total=3,
                read=3,
                connect=3,
                backoff_factor=1.5,
                status_forcelist=[500, 502, 503, 504, 429, 408]
            )
            adapter = HTTPAdapter(max_retries=retry_strategy, pool_connections=10, pool_maxsize=20)
            self.session.mount("http://", adapter)
            self.session.mount("https://", adapter)
            
            # Better headers
            self.session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
            })
'''
            
            # Find __init__ method and add session enhancement
            init_pattern = r'(def __init__\(self[^)]*\):.*?\n)(.*?)(\n\s*def|\nclass|\Z)'
            
            def add_session_enhancement(match):
                init_def = match.group(1)
                init_body = match.group(2)
                next_part = match.group(3)
                
                # Add session enhancement at the end of __init__
                enhanced_init = init_def + init_body + session_enhancement + next_part
                return enhanced_init
            
            new_content = re.sub(init_pattern, add_session_enhancement, content, flags=re.DOTALL)
            
            if new_content != content:
                if self.backup_file(file_path):
                    file_path.write_text(new_content)
                    logger.info(f"✅ Added retry logic to {file_path}")
                    return True
                else:
                    logger.error(f"❌ Could not backup {file_path} for retry logic")
                    return False
            else:
                logger.info(f"ℹ️  Could not find suitable location for retry logic in {file_path}")
                return True
                
        except Exception as e:
            logger.error(f"❌ Failed to add retry logic to {file_path}: {e}")
            return False
    
    def patch_all_scrapers(self):
        """Patch all known scraper files"""
        if not self.find_gpt_researcher_path():
            return False
        
        # Known scraper file paths relative to gpt_researcher root
        scraper_files = [
            'scraper/beautiful_soup/beautiful_soup.py',
            'scraper/tavily_extract/tavily_extract.py', 
            'scraper/firecrawl/firecrawl.py',
        ]
        
        patched_count = 0
        total_files = 0
        
        for scraper_file in scraper_files:
            file_path = self.gpt_researcher_path / scraper_file
            
            if file_path.exists():
                total_files += 1
                logger.info(f"🔧 Patching {scraper_file}...")
                
                # Patch timeouts
                timeout_success = self.patch_timeout_in_file(file_path)
                
                # Add retry logic 
                retry_success = self.add_retry_logic_to_file(file_path)
                
                if timeout_success and retry_success:
                    patched_count += 1
                    logger.info(f"✅ Successfully patched {scraper_file}")
                else:
                    logger.warning(f"⚠️  Partial patch for {scraper_file}")
                    
            else:
                logger.warning(f"⚠️  Scraper file not found: {file_path}")
        
        logger.info(f"📊 Patching complete: {patched_count}/{total_files} files successfully patched")
        return patched_count > 0
    
    def restore_backups(self):
        """Restore all backup files (undo patches)"""
        if not self.find_gpt_researcher_path():
            return False
        
        backup_files = list(self.gpt_researcher_path.rglob(f'*{self.backup_suffix}'))
        restored_count = 0
        
        for backup_file in backup_files:
            original_file = Path(str(backup_file).replace(self.backup_suffix, ''))
            
            try:
                original_file.write_text(backup_file.read_text())
                backup_file.unlink()  # Delete backup after restore
                logger.info(f"✅ Restored {original_file}")
                restored_count += 1
            except Exception as e:
                logger.error(f"❌ Failed to restore {original_file}: {e}")
        
        logger.info(f"📊 Restore complete: {restored_count} files restored")
        return restored_count > 0


def apply_direct_timeout_patches():
    """Main function to apply direct timeout patches"""
    patcher = DirectTimeoutPatcher()
    
    logger.info("🚀 Applying direct timeout patches to gpt-researcher...")
    
    success = patcher.patch_all_scrapers()
    
    if success:
        logger.info("✅ Direct timeout patches applied successfully!")
        logger.info("📋 Changes made:")
        logger.info("   • timeout=4 changed to timeout=30 in scraper files")
        logger.info("   • Added retry logic with exponential backoff")
        logger.info("   • Enhanced connection pooling")
        logger.info("   • Improved browser headers")
        return True
    else:
        logger.error("❌ Failed to apply direct timeout patches")
        return False


def restore_original_files():
    """Restore original gpt-researcher files"""
    patcher = DirectTimeoutPatcher()
    
    logger.info("🔄 Restoring original gpt-researcher files...")
    success = patcher.restore_backups()
    
    if success:
        logger.info("✅ Original files restored successfully!")
    else:
        logger.warning("⚠️  No backup files found or restore failed")
    
    return success


if __name__ == "__main__":
    import sys
    
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    if len(sys.argv) > 1 and sys.argv[1] == '--restore':
        restore_original_files()
    else:
        apply_direct_timeout_patches()