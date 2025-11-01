"""
Unit tests for filename_utils module.

Tests the centralized filename parsing and validation logic
that replaces 47+ scattered functions across the codebase.

Test Coverage:
- FilenameParser: All parsing methods
- ParsedFilename: Properties and methods
- SecurePathValidator: All security validation
- Edge cases: Invalid inputs, malicious patterns
- Backward compatibility: Convenience functions

Author: TK9 Team
Date: 2025-11-02
"""

import pytest
from pathlib import Path
import sys
from typing import Optional

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from filename_utils import (
    FileType,
    Language,
    ParsedFilename,
    FilenameParser,
    SecurePathValidator,
    # Convenience functions
    parse_filename,
    extract_file_type,
    extract_language,
    to_friendly_name,
    validate_safe_path,
)


# ============================================================================
# Enum Tests
# ============================================================================

class TestFileType:
    """Test FileType enum"""

    def test_file_type_values(self):
        """Test all enum values exist"""
        assert FileType.PDF.value == "pdf"
        assert FileType.DOCX.value == "docx"
        assert FileType.MARKDOWN.value == "md"
        assert FileType.UNKNOWN.value == "unknown"

    def test_extension_property(self):
        """Test extension property returns dot-prefixed extension"""
        assert FileType.PDF.extension == ".pdf"
        assert FileType.DOCX.extension == ".docx"
        assert FileType.MARKDOWN.extension == ".md"

    def test_mime_type_property(self):
        """Test MIME type mapping"""
        assert FileType.PDF.mime_type == "application/pdf"
        assert FileType.DOCX.mime_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        assert FileType.MARKDOWN.mime_type == "text/markdown"
        assert FileType.UNKNOWN.mime_type == "application/octet-stream"


class TestLanguage:
    """Test Language enum"""

    def test_language_values(self):
        """Test all enum values exist"""
        assert Language.ENGLISH.value == "en"
        assert Language.VIETNAMESE.value == "vi"
        assert Language.SPANISH.value == "es"
        assert Language.FRENCH.value == "fr"

    def test_from_code_valid(self):
        """Test parsing valid language codes"""
        assert Language.from_code("vi") == Language.VIETNAMESE
        assert Language.from_code("en") == Language.ENGLISH
        assert Language.from_code("es") == Language.SPANISH
        assert Language.from_code("fr") == Language.FRENCH

    def test_from_code_case_insensitive(self):
        """Test case-insensitive parsing"""
        assert Language.from_code("VI") == Language.VIETNAMESE
        assert Language.from_code("En") == Language.ENGLISH

    def test_from_code_invalid(self):
        """Test invalid codes default to English"""
        assert Language.from_code("xx") == Language.ENGLISH
        assert Language.from_code("invalid") == Language.ENGLISH
        assert Language.from_code(None) == Language.ENGLISH
        assert Language.from_code("") == Language.ENGLISH


# ============================================================================
# ParsedFilename Tests
# ============================================================================

class TestParsedFilename:
    """Test ParsedFilename dataclass"""

    def test_friendly_name_original(self):
        """Test friendly name for original files"""
        parsed = ParsedFilename(
            uuid="72320175ea5448e7a3f5116b95532853",
            language=Language.ENGLISH,
            file_type=FileType.PDF,
            is_translated=False,
            original_filename="72320175ea5448e7a3f5116b95532853.pdf"
        )
        assert parsed.friendly_name == "research_report.pdf"

    def test_friendly_name_translated(self):
        """Test friendly name for translated files"""
        parsed = ParsedFilename(
            uuid="72320175ea5448e7a3f5116b95532853",
            language=Language.VIETNAMESE,
            file_type=FileType.PDF,
            is_translated=True,
            original_filename="72320175ea5448e7a3f5116b95532853_vi.pdf"
        )
        assert parsed.friendly_name == "research_report_vi.pdf"

    def test_sort_priority_original(self):
        """Test sort priority for original files"""
        parsed = ParsedFilename(
            uuid="72320175ea5448e7",
            language=Language.ENGLISH,
            file_type=FileType.PDF,
            is_translated=False,
            original_filename="test.pdf"
        )
        assert parsed.sort_priority == 0

    def test_sort_priority_translated(self):
        """Test sort priority for translated files"""
        parsed = ParsedFilename(
            uuid="72320175ea5448e7",
            language=Language.VIETNAMESE,
            file_type=FileType.PDF,
            is_translated=True,
            original_filename="test_vi.pdf"
        )
        assert parsed.sort_priority == 1

    def test_properties(self):
        """Test all properties"""
        parsed = ParsedFilename(
            uuid="72320175ea5448e7",
            language=Language.ENGLISH,
            file_type=FileType.PDF,
            is_translated=False,
            original_filename="test.pdf"
        )
        assert parsed.extension == ".pdf"
        assert parsed.mime_type == "application/pdf"


# ============================================================================
# FilenameParser.parse() Tests
# ============================================================================

class TestFilenameParserParse:
    """Test FilenameParser.parse() - Core parsing logic"""

    def test_parse_original_pdf(self):
        """Test parsing original PDF file"""
        parsed = FilenameParser.parse("72320175ea5448e7a3f5116b95532853.pdf")
        assert parsed is not None
        assert parsed.uuid == "72320175ea5448e7a3f5116b95532853"
        assert parsed.language == Language.ENGLISH
        assert parsed.file_type == FileType.PDF
        assert parsed.is_translated is False

    def test_parse_translated_pdf(self):
        """Test parsing Vietnamese translated PDF"""
        parsed = FilenameParser.parse("72320175ea5448e7a3f5116b95532853_vi.pdf")
        assert parsed is not None
        assert parsed.uuid == "72320175ea5448e7a3f5116b95532853"
        assert parsed.language == Language.VIETNAMESE
        assert parsed.file_type == FileType.PDF
        assert parsed.is_translated is True

    def test_parse_all_file_types(self):
        """Test parsing all supported file types"""
        uuid = "72320175ea5448e7a3f5116b95532853"

        # PDF
        parsed = FilenameParser.parse(f"{uuid}.pdf")
        assert parsed.file_type == FileType.PDF

        # DOCX
        parsed = FilenameParser.parse(f"{uuid}.docx")
        assert parsed.file_type == FileType.DOCX

        # Markdown
        parsed = FilenameParser.parse(f"{uuid}.md")
        assert parsed.file_type == FileType.MARKDOWN

    def test_parse_all_languages(self):
        """Test parsing all supported languages"""
        uuid = "72320175ea5448e7a3f5116b95532853"

        # Vietnamese
        parsed = FilenameParser.parse(f"{uuid}_vi.pdf")
        assert parsed.language == Language.VIETNAMESE

        # Spanish
        parsed = FilenameParser.parse(f"{uuid}_es.pdf")
        assert parsed.language == Language.SPANISH

        # French
        parsed = FilenameParser.parse(f"{uuid}_fr.pdf")
        assert parsed.language == Language.FRENCH

    def test_parse_case_insensitive(self):
        """Test case-insensitive parsing"""
        # Uppercase UUID
        parsed = FilenameParser.parse("72320175EA5448E7A3F5116B95532853.PDF")
        assert parsed is not None
        assert parsed.uuid == "72320175ea5448e7a3f5116b95532853"  # Normalized to lowercase

        # Mixed case language
        parsed = FilenameParser.parse("72320175ea5448e7a3f5116b95532853_VI.pdf")
        assert parsed.language == Language.VIETNAMESE

    def test_parse_invalid_uuid_length(self):
        """Test invalid UUID length"""
        # Too short
        assert FilenameParser.parse("1234.pdf") is None

        # Too long
        assert FilenameParser.parse("72320175ea5448e7a3f5116b95532853123.pdf") is None

    def test_parse_invalid_uuid_characters(self):
        """Test invalid UUID characters"""
        # Non-hex characters
        assert FilenameParser.parse("72320175ea5448g7a3f5116b95532853.pdf") is None
        assert FilenameParser.parse("72320175-ea54-48e7-a3f5-116b95532853.pdf") is None

    def test_parse_no_extension(self):
        """Test filename without extension"""
        assert FilenameParser.parse("72320175ea5448e7a3f5116b95532853") is None

    def test_parse_empty_string(self):
        """Test empty string"""
        assert FilenameParser.parse("") is None
        assert FilenameParser.parse(None) is None

    def test_parse_unsupported_extension(self):
        """Test unsupported extension (should parse but mark as UNKNOWN)"""
        parsed = FilenameParser.parse("72320175ea5448e7a3f5116b95532853.exe")
        assert parsed is not None  # Regex matches
        assert parsed.file_type == FileType.UNKNOWN  # But marked as unknown

    def test_parse_invalid_language_code(self):
        """Test invalid language code defaults to English"""
        parsed = FilenameParser.parse("72320175ea5448e7a3f5116b95532853_xx.pdf")
        assert parsed is not None
        assert parsed.language == Language.ENGLISH  # Defaults to English
        assert parsed.is_translated is True  # Still has underscore


# ============================================================================
# FilenameParser.extract_file_type() Tests
# ============================================================================

class TestFilenameParserExtractFileType:
    """Test multi-layer file type extraction"""

    def test_extract_from_valid_uuid_filename(self):
        """Test extraction from valid UUID filename"""
        assert FilenameParser.extract_file_type("72320175ea5448e7a3f5116b95532853.pdf") == FileType.PDF
        assert FilenameParser.extract_file_type("72320175ea5448e7a3f5116b95532853_vi.docx") == FileType.DOCX
        assert FilenameParser.extract_file_type("72320175ea5448e7a3f5116b95532853.md") == FileType.MARKDOWN

    def test_extract_from_simple_filename(self):
        """Test fallback to simple extension extraction"""
        assert FilenameParser.extract_file_type("report.pdf") == FileType.PDF
        assert FilenameParser.extract_file_type("document.docx") == FileType.DOCX
        assert FilenameParser.extract_file_type("readme.md") == FileType.MARKDOWN

    def test_extract_from_url(self):
        """Test fallback to URL extraction"""
        result = FilenameParser.extract_file_type(
            "invalid_name",
            "/download/session-123/72320175ea5448e7.pdf"
        )
        assert result == FileType.PDF

    def test_extract_unknown_extension(self):
        """Test unknown extension returns UNKNOWN"""
        assert FilenameParser.extract_file_type("file.exe") == FileType.UNKNOWN
        assert FilenameParser.extract_file_type("file.xyz") == FileType.UNKNOWN

    def test_extract_no_extension(self):
        """Test no extension returns UNKNOWN"""
        assert FilenameParser.extract_file_type("no_extension") == FileType.UNKNOWN


# ============================================================================
# FilenameParser.extract_language() Tests
# ============================================================================

class TestFilenameParserExtractLanguage:
    """Test language extraction"""

    def test_extract_original_file(self):
        """Test original files default to English"""
        assert FilenameParser.extract_language("72320175ea5448e7.pdf") == Language.ENGLISH

    def test_extract_translated_files(self):
        """Test translated files detect language"""
        assert FilenameParser.extract_language("72320175ea5448e7a3f5116b95532853_vi.pdf") == Language.VIETNAMESE
        assert FilenameParser.extract_language("72320175ea5448e7a3f5116b95532853_es.pdf") == Language.SPANISH
        assert FilenameParser.extract_language("72320175ea5448e7a3f5116b95532853_fr.pdf") == Language.FRENCH

    def test_extract_invalid_filename(self):
        """Test invalid filename defaults to English"""
        assert FilenameParser.extract_language("invalid.pdf") == Language.ENGLISH


# ============================================================================
# FilenameParser Helper Methods Tests
# ============================================================================

class TestFilenameParserHelpers:
    """Test helper methods"""

    def test_is_translated(self):
        """Test translation detection"""
        assert FilenameParser.is_translated("72320175ea5448e7a3f5116b95532853_vi.pdf") is True
        assert FilenameParser.is_translated("72320175ea5448e7a3f5116b95532853.pdf") is False

    def test_get_sort_priority(self):
        """Test sort priority"""
        assert FilenameParser.get_sort_priority("72320175ea5448e7a3f5116b95532853.pdf") == 0  # Original
        assert FilenameParser.get_sort_priority("72320175ea5448e7a3f5116b95532853_vi.pdf") == 1  # Translated

    def test_to_friendly_name(self):
        """Test friendly name conversion"""
        assert FilenameParser.to_friendly_name("72320175ea5448e7a3f5116b95532853.pdf") == "research_report.pdf"
        assert FilenameParser.to_friendly_name("72320175ea5448e7a3f5116b95532853_vi.pdf") == "research_report_vi.pdf"
        assert FilenameParser.to_friendly_name("72320175ea5448e7a3f5116b95532853_es.docx") == "research_report_es.docx"

    def test_get_mime_type(self):
        """Test MIME type detection"""
        assert FilenameParser.get_mime_type("report.pdf") == "application/pdf"
        assert FilenameParser.get_mime_type("report.docx") == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        assert FilenameParser.get_mime_type("report.md") == "text/markdown"

    def test_is_valid(self):
        """Test filename validation"""
        assert FilenameParser.is_valid("report.pdf") is True
        assert FilenameParser.is_valid("report.docx") is True
        assert FilenameParser.is_valid("report.md") is True
        assert FilenameParser.is_valid("report.exe") is False
        assert FilenameParser.is_valid("no_extension") is False
        assert FilenameParser.is_valid("") is False


# ============================================================================
# SecurePathValidator Tests
# ============================================================================

class TestSecurePathValidator:
    """Test security validation"""

    def test_validate_session_id_valid(self):
        """Test valid session IDs"""
        assert SecurePathValidator.validate_session_id("550e8400-e29b-41d4-a716-446655440000") is True
        assert SecurePathValidator.validate_session_id("session_123") is True
        assert SecurePathValidator.validate_session_id("abc123def456") is True

    def test_validate_session_id_invalid(self):
        """Test invalid session IDs"""
        assert SecurePathValidator.validate_session_id("../etc/passwd") is False
        assert SecurePathValidator.validate_session_id("/absolute/path") is False
        assert SecurePathValidator.validate_session_id("session/subdir") is False
        assert SecurePathValidator.validate_session_id("") is False
        assert SecurePathValidator.validate_session_id(None) is False

    def test_validate_filename_valid(self):
        """Test valid filenames"""
        assert SecurePathValidator.validate_filename("report.pdf") is True
        assert SecurePathValidator.validate_filename("72320175ea5448e7.pdf") is True
        assert SecurePathValidator.validate_filename("file_name_123.docx") is True

    def test_validate_filename_invalid(self):
        """Test invalid filenames (path traversal attempts)"""
        assert SecurePathValidator.validate_filename("../etc/passwd") is False
        assert SecurePathValidator.validate_filename("subdir/file.pdf") is False
        assert SecurePathValidator.validate_filename("..\\windows\\system32") is False
        assert SecurePathValidator.validate_filename("") is False
        assert SecurePathValidator.validate_filename(None) is False

    def test_validate_file_path_valid(self):
        """Test valid file paths"""
        assert SecurePathValidator.validate_file_path("outputs/session/file.pdf") is True
        assert SecurePathValidator.validate_file_path("relative/path/file.pdf") is True

    def test_validate_file_path_invalid(self):
        """Test invalid file paths"""
        assert SecurePathValidator.validate_file_path("/absolute/path/file.pdf") is False
        assert SecurePathValidator.validate_file_path("../parent/file.pdf") is False
        assert SecurePathValidator.validate_file_path("") is False
        assert SecurePathValidator.validate_file_path(None) is False

    def test_resolve_safe_path_valid(self, tmp_path):
        """Test safe path resolution"""
        base_dir = tmp_path / "outputs"
        base_dir.mkdir()

        session_id = "550e8400-e29b-41d4-a716"
        filename = "report.pdf"

        result = SecurePathValidator.resolve_safe_path(base_dir, session_id, filename)
        assert result is not None
        assert result.parent.name == session_id
        assert result.name == filename

    def test_resolve_safe_path_invalid_session_id(self, tmp_path):
        """Test path resolution rejects invalid session ID"""
        base_dir = tmp_path / "outputs"
        base_dir.mkdir()

        result = SecurePathValidator.resolve_safe_path(base_dir, "../etc", "passwd")
        assert result is None

    def test_resolve_safe_path_invalid_filename(self, tmp_path):
        """Test path resolution rejects invalid filename"""
        base_dir = tmp_path / "outputs"
        base_dir.mkdir()

        result = SecurePathValidator.resolve_safe_path(base_dir, "550e8400", "../passwd")
        assert result is None

    def test_resolve_safe_path_traversal_blocked(self, tmp_path):
        """Test path traversal is blocked"""
        base_dir = tmp_path / "outputs"
        base_dir.mkdir()

        # Even if session_id and filename look valid individually,
        # the resolved path must be within base_dir
        # This is tested by pathlib.resolve() logic

        result = SecurePathValidator.resolve_safe_path(base_dir, "550e8400", "file.pdf")
        assert result is not None  # Valid path

        # Path traversal attempts will be caught by validation
        result = SecurePathValidator.resolve_safe_path(base_dir, "550e8400", "../../etc/passwd")
        assert result is None  # Invalid filename


# ============================================================================
# Convenience Functions Tests
# ============================================================================

class TestConvenienceFunctions:
    """Test convenience wrapper functions"""

    def test_parse_filename_wrapper(self):
        """Test parse_filename convenience function"""
        result = parse_filename("72320175ea5448e7a3f5116b95532853.pdf")
        assert result is not None
        assert result.file_type == FileType.PDF

    def test_extract_file_type_wrapper(self):
        """Test extract_file_type convenience function"""
        assert extract_file_type("report.pdf") == FileType.PDF

    def test_extract_language_wrapper(self):
        """Test extract_language convenience function"""
        assert extract_language("72320175ea5448e7a3f5116b95532853_vi.pdf") == Language.VIETNAMESE

    def test_to_friendly_name_wrapper(self):
        """Test to_friendly_name convenience function"""
        assert to_friendly_name("72320175ea5448e7a3f5116b95532853.pdf") == "research_report.pdf"

    def test_validate_safe_path_wrapper(self, tmp_path):
        """Test validate_safe_path convenience function"""
        base_dir = tmp_path / "outputs"
        base_dir.mkdir()

        result = validate_safe_path(base_dir, "550e8400", "report.pdf")
        assert result is not None


# ============================================================================
# Integration Tests
# ============================================================================

class TestIntegration:
    """End-to-end integration tests"""

    def test_full_workflow_original_file(self):
        """Test complete workflow for original file"""
        filename = "72320175ea5448e7a3f5116b95532853.pdf"

        # Parse
        parsed = FilenameParser.parse(filename)
        assert parsed is not None

        # Properties
        assert parsed.is_translated is False
        assert parsed.language == Language.ENGLISH
        assert parsed.file_type == FileType.PDF
        assert parsed.friendly_name == "research_report.pdf"
        assert parsed.sort_priority == 0

        # Helper methods
        assert FilenameParser.extract_file_type(filename) == FileType.PDF
        assert FilenameParser.extract_language(filename) == Language.ENGLISH
        assert FilenameParser.is_translated(filename) is False
        assert FilenameParser.to_friendly_name(filename) == "research_report.pdf"
        assert FilenameParser.get_mime_type(filename) == "application/pdf"
        assert FilenameParser.is_valid(filename) is True

    def test_full_workflow_translated_file(self):
        """Test complete workflow for translated file"""
        filename = "72320175ea5448e7a3f5116b95532853_vi.pdf"

        # Parse
        parsed = FilenameParser.parse(filename)
        assert parsed is not None

        # Properties
        assert parsed.is_translated is True
        assert parsed.language == Language.VIETNAMESE
        assert parsed.file_type == FileType.PDF
        assert parsed.friendly_name == "research_report_vi.pdf"
        assert parsed.sort_priority == 1

        # Helper methods
        assert FilenameParser.extract_file_type(filename) == FileType.PDF
        assert FilenameParser.extract_language(filename) == Language.VIETNAMESE
        assert FilenameParser.is_translated(filename) is True
        assert FilenameParser.to_friendly_name(filename) == "research_report_vi.pdf"
        assert FilenameParser.get_mime_type(filename) == "application/pdf"
        assert FilenameParser.is_valid(filename) is True

    def test_sorting_original_before_translated(self):
        """Test that original files sort before translated files"""
        filenames = [
            "72320175ea5448e7a3f5116b95532853_vi.pdf",
            "72320175ea5448e7a3f5116b95532853.pdf",
            "72320175ea5448e7a3f5116b95532853_es.pdf",
            "72320175ea5448e7a3f5116b95532853.md",
            "72320175ea5448e7a3f5116b95532853_vi.md",
        ]

        # Sort by priority then name
        sorted_filenames = sorted(
            filenames,
            key=lambda f: (FilenameParser.get_sort_priority(f), f)
        )

        # Original files should come first
        assert sorted_filenames[0] == "72320175ea5448e7a3f5116b95532853.md"
        assert sorted_filenames[1] == "72320175ea5448e7a3f5116b95532853.pdf"
        # Translated files after
        assert sorted_filenames[2] == "72320175ea5448e7a3f5116b95532853_es.pdf"
        assert sorted_filenames[3] == "72320175ea5448e7a3f5116b95532853_vi.md"
        assert sorted_filenames[4] == "72320175ea5448e7a3f5116b95532853_vi.pdf"
