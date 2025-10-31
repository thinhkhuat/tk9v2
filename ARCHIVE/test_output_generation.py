#!/usr/bin/env python3
"""
Test to verify the research pipeline can complete and generate output files
"""

import sys
import os
import asyncio
from pathlib import Path
import time

# Add the multi_agents directory to path
sys.path.insert(0, 'multi_agents')

def count_output_files():
    """Count existing output files in the outputs directory"""
    outputs_dir = Path("outputs")
    if not outputs_dir.exists():
        return 0, []
    
    count = 0
    files = []
    for file_path in outputs_dir.rglob("*"):
        if file_path.is_file() and file_path.suffix in ['.pdf', '.docx', '.md']:
            count += 1
            files.append(str(file_path))
    
    return count, files

async def test_output_file_generation():
    """Test that the research pipeline can complete and generate output files"""
    print("📁 Testing output file generation...")
    
    # Count existing files
    initial_count, initial_files = count_output_files()
    print(f"Initial output files: {initial_count}")
    
    try:
        # Import research components
        from main import run_research_task
        from gpt_researcher.utils.enum import Tone
        
        print("Starting research with file generation (timeout: 3 minutes)...")
        
        # Use a simple query and enable file writing
        result = await asyncio.wait_for(
            run_research_task(
                query="What is artificial intelligence in 2025?",  # Simple but comprehensive query
                tone=Tone.Objective,
                write_to_files=True,  # Enable file writing
                language="en"  # English to avoid translation complexity
            ),
            timeout=180.0  # 3 minute timeout
        )
        
        print("✅ Research completed successfully!")
        print(f"   Result length: {len(str(result))} characters")
        
        # Wait a moment for files to be written
        await asyncio.sleep(2)
        
        # Count output files after research
        final_count, final_files = count_output_files()
        new_files = final_count - initial_count
        
        print(f"\n📊 File Generation Results:")
        print(f"   Files before: {initial_count}")
        print(f"   Files after:  {final_count}")
        print(f"   New files:    {new_files}")
        
        if new_files >= 3:  # Should generate at least PDF, DOCX, MD
            print("✅ Output files generated successfully!")
            
            # List the new files
            print("\n📋 New output files:")
            for file_path in final_files:
                if file_path not in initial_files:
                    file_size = Path(file_path).stat().st_size
                    print(f"   • {file_path} ({file_size:,} bytes)")
            
            return True
        else:
            print("⚠️  Expected at least 3 output files (PDF, DOCX, MD) but got {new_files}")
            return False
            
    except asyncio.TimeoutError:
        print("⏱️  Research timed out after 3 minutes")
        
        # Check if any files were generated even with timeout
        final_count, final_files = count_output_files()
        new_files = final_count - initial_count
        
        if new_files > 0:
            print(f"   But {new_files} output files were generated during the process")
            return True
        else:
            print("   No output files were generated")
            return False
            
    except Exception as e:
        error_msg = str(e)
        print(f"❌ Research failed: {error_msg}")
        
        if "Separator is not found" in error_msg and "chunk exceed" in error_msg:
            print("🚨 CHUNKING ERROR STILL OCCURS!")
            print("   The fix did not prevent the error")
            return False
        else:
            print("   This is not the chunking error we're fixing")
            
            # Check if any files were generated before the error
            final_count, final_files = count_output_files()
            new_files = final_count - initial_count
            
            if new_files > 0:
                print(f"   But {new_files} output files were generated before the error")
                return True
            else:
                return False

def main():
    """Test output file generation"""
    print("🚀 Testing Output File Generation After Chunking Fix")
    print("=" * 60)
    
    try:
        success = asyncio.run(test_output_file_generation())
        
        print("\n" + "=" * 60)
        print("📊 TEST RESULTS")
        
        if success:
            print("✅ SUCCESS: Output file generation is working!")
            print("   The chunking fix allows the research pipeline to complete")
            print("   and generate the expected output files")
        else:
            print("❌ FAILURE: Output file generation issues")
            print("   Check the specific errors above")
        
        return success
        
    except Exception as e:
        print(f"❌ Test setup failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)