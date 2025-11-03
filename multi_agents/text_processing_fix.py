#!/usr/bin/env python3
"""
Text Processing Fix for Chunking Errors
Implements defensive programming to prevent "Separator is not found, and chunk exceed the limit" errors
"""

import logging
import re
from typing import List

logger = logging.getLogger(__name__)


class TextChunkingFix:
    """
    Defensive text processing to prevent chunking errors
    """

    def __init__(self):
        self.max_chunk_size = 800  # Conservative chunk size
        self.max_overlap = 50  # Conservative overlap
        self.backup_separators = ["\n\n", "\n", ". ", "? ", "! ", ", ", " ", ""]

    def safe_text_split(
        self, text: str, chunk_size: int = None, chunk_overlap: int = None
    ) -> List[str]:
        """
        Safely split text into chunks with robust error handling

        Args:
            text: Input text to split
            chunk_size: Maximum chunk size (defaults to 800)
            chunk_overlap: Overlap between chunks (defaults to 50)

        Returns:
            List of text chunks
        """
        if not text or not isinstance(text, str):
            return []

        chunk_size = chunk_size or self.max_chunk_size
        chunk_overlap = chunk_overlap or self.max_overlap

        # If text is smaller than chunk size, return as single chunk
        if len(text) <= chunk_size:
            return [text]

        try:
            # Try using LangChain's splitter first
            from langchain.text_splitter import RecursiveCharacterTextSplitter

            splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                separators=self.backup_separators,
                length_function=len,
                is_separator_regex=False,
            )

            chunks = splitter.split_text(text)

            # Validate chunks
            validated_chunks = []
            for chunk in chunks:
                if chunk and isinstance(chunk, str) and len(chunk.strip()) > 0:
                    # Ensure chunk doesn't exceed size limit
                    if len(chunk) > chunk_size * 1.5:  # Allow 50% overflow for edge cases
                        # Force split oversized chunks
                        subchunks = self._force_split_text(chunk, chunk_size)
                        validated_chunks.extend(subchunks)
                    else:
                        validated_chunks.append(chunk.strip())

            return validated_chunks if validated_chunks else [text]

        except Exception as e:
            logger.warning(f"LangChain text splitter failed: {e}, using fallback method")
            return self._fallback_text_split(text, chunk_size, chunk_overlap)

    def _fallback_text_split(self, text: str, chunk_size: int, chunk_overlap: int) -> List[str]:
        """
        Fallback text splitting method when LangChain fails
        """
        chunks = []

        # Clean the text first
        text = self._clean_text(text)

        # Try splitting by paragraphs first
        paragraphs = text.split("\n\n")

        current_chunk = ""

        for paragraph in paragraphs:
            # If adding this paragraph would exceed chunk size
            if len(current_chunk) + len(paragraph) > chunk_size:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    # Add overlap from the end of current chunk
                    if chunk_overlap > 0 and len(current_chunk) > chunk_overlap:
                        overlap = current_chunk[-chunk_overlap:]
                        current_chunk = overlap + "\n\n" + paragraph
                    else:
                        current_chunk = paragraph
                else:
                    # Paragraph itself is too long, force split
                    if len(paragraph) > chunk_size:
                        subchunks = self._force_split_text(paragraph, chunk_size)
                        chunks.extend(subchunks[:-1])  # Add all but last
                        current_chunk = subchunks[-1]  # Last becomes current
                    else:
                        current_chunk = paragraph
            else:
                # Add paragraph to current chunk
                if current_chunk:
                    current_chunk += "\n\n" + paragraph
                else:
                    current_chunk = paragraph

        # Add the last chunk
        if current_chunk.strip():
            chunks.append(current_chunk.strip())

        return chunks if chunks else [text[:chunk_size]]

    def _force_split_text(self, text: str, max_size: int) -> List[str]:
        """
        Force split text that's too long, preserving word boundaries when possible
        """
        if len(text) <= max_size:
            return [text]

        chunks = []
        remaining = text

        while remaining:
            if len(remaining) <= max_size:
                chunks.append(remaining)
                break

            # Try to split at word boundary
            chunk = remaining[:max_size]

            # Find the last space within the chunk
            last_space = chunk.rfind(" ")

            if last_space > max_size * 0.5:  # Only use space if it's not too early
                split_point = last_space
            else:
                # No good space found, split at max_size
                split_point = max_size

            chunk = remaining[:split_point]
            chunks.append(chunk.strip())
            remaining = remaining[split_point:].lstrip()

        return [c for c in chunks if c.strip()]

    def _clean_text(self, text: str) -> str:
        """
        Clean text to prevent processing issues
        """
        if not text:
            return ""

        # Remove excessive whitespace
        text = re.sub(r"\s+", " ", text)

        # Remove control characters but keep basic punctuation
        text = re.sub(r"[\x00-\x1f\x7f-\x9f]", "", text)

        # Ensure text doesn't start/end with whitespace
        text = text.strip()

        return text

    def validate_text_for_processing(self, text: str, max_length: int = 50000) -> tuple[bool, str]:
        """
        Validate text before processing to prevent chunking errors

        Returns:
            Tuple of (is_valid, cleaned_text_or_error_message)
        """
        if not text:
            return False, "Empty text"

        if not isinstance(text, str):
            try:
                text = str(text)
            except Exception:
                return False, "Cannot convert to string"

        # Check length
        if len(text) > max_length:
            logger.warning(f"Text too long ({len(text)} chars), truncating to {max_length}")
            text = text[:max_length]

        # Clean the text
        cleaned_text = self._clean_text(text)

        if len(cleaned_text) < 10:  # Too short to be meaningful
            return False, "Text too short after cleaning"

        return True, cleaned_text


class ChunkingErrorPrevention:
    """
    Monkey patch and defensive wrapper for text processing in the research pipeline
    """

    def __init__(self):
        self.text_fixer = TextChunkingFix()

    def patch_gpt_researcher_compression(self):
        """
        Patch GPT-researcher's compression module to use safe chunking
        """
        try:
            import gpt_researcher.context.compression as compression_module

            # Store original class
            original_compressor = compression_module.ContextCompressor
            text_fixer = self.text_fixer

            class SafeContextCompressor(original_compressor):
                """Enhanced context compressor with chunking error prevention"""

                def __get_contextual_retriever(self):
                    """Override with safer text splitter configuration"""
                    try:
                        from langchain.retrievers import ContextualCompressionRetriever
                        from langchain.retrievers.document_compressors import (
                            DocumentCompressorPipeline,
                            EmbeddingsFilter,
                        )
                        from langchain.text_splitter import RecursiveCharacterTextSplitter

                        from ..context.retriever import SearchAPIRetriever

                        # Use conservative chunking parameters
                        splitter = RecursiveCharacterTextSplitter(
                            chunk_size=800,  # Reduced from 1000
                            chunk_overlap=50,  # Reduced from 100
                            separators=text_fixer.backup_separators,
                            length_function=len,
                            is_separator_regex=False,
                        )

                        relevance_filter = EmbeddingsFilter(
                            embeddings=self.embeddings,
                            similarity_threshold=self.similarity_threshold,
                        )

                        pipeline_compressor = DocumentCompressorPipeline(
                            transformers=[splitter, relevance_filter]
                        )

                        base_retriever = SearchAPIRetriever(pages=self.documents)

                        contextual_retriever = ContextualCompressionRetriever(
                            base_compressor=pipeline_compressor, base_retriever=base_retriever
                        )

                        return contextual_retriever

                    except Exception as e:
                        logger.error(f"Error creating safe contextual retriever: {e}")
                        # Fallback to original method
                        return super().__get_contextual_retriever()

                async def async_get_context(self, query, max_results=5, cost_callback=None):
                    """Enhanced context retrieval with error handling"""
                    try:
                        # Validate query first
                        is_valid, cleaned_query = text_fixer.validate_text_for_processing(query)
                        if not is_valid:
                            logger.warning(f"Invalid query: {cleaned_query}")
                            return ""

                        # Pre-process documents to prevent chunking issues
                        safe_documents = []
                        for doc in self.documents:
                            if hasattr(doc, "page_content"):
                                is_valid, cleaned_content = text_fixer.validate_text_for_processing(
                                    doc.page_content
                                )
                                if is_valid:
                                    # Create a copy with cleaned content
                                    safe_doc = doc
                                    safe_doc.page_content = cleaned_content
                                    safe_documents.append(safe_doc)
                            else:
                                safe_documents.append(doc)

                        # Temporarily replace documents
                        original_documents = self.documents
                        self.documents = safe_documents

                        try:
                            result = await super().async_get_context(
                                cleaned_query, max_results, cost_callback
                            )
                            return result
                        finally:
                            # Restore original documents
                            self.documents = original_documents

                    except Exception as e:
                        error_msg = str(e)
                        if "Separator is not found" in error_msg or "chunk exceed" in error_msg:
                            logger.warning(f"Chunking error caught and handled: {error_msg}")
                            # Return empty context rather than failing
                            return ""
                        else:
                            raise e

            # Replace the class
            compression_module.ContextCompressor = SafeContextCompressor

            logger.info("✅ GPT-researcher compression module patched for chunking safety")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to patch compression module: {e}")
            return False

    def patch_langchain_text_splitter(self):
        """
        Patch LangChain text splitter to be more defensive
        """
        try:
            from langchain.text_splitter import RecursiveCharacterTextSplitter

            # Store original method
            original_split_text = RecursiveCharacterTextSplitter.split_text
            text_fixer = self.text_fixer

            def safe_split_text(self, text: str) -> List[str]:
                """Enhanced split_text with error handling"""
                try:
                    # Validate input
                    is_valid, cleaned_text = text_fixer.validate_text_for_processing(text)
                    if not is_valid:
                        logger.warning(f"Text validation failed: {cleaned_text}")
                        return []

                    # Use conservative chunk size if current settings are too aggressive
                    if hasattr(self, "_chunk_size") and self._chunk_size > 1000:
                        logger.warning(f"Chunk size too large ({self._chunk_size}), using 800")
                        self._chunk_size = 800

                    if hasattr(self, "_chunk_overlap") and self._chunk_overlap > 100:
                        logger.warning(f"Chunk overlap too large ({self._chunk_overlap}), using 50")
                        self._chunk_overlap = 50

                    # Call original method
                    result = original_split_text(self, cleaned_text)

                    # Validate result
                    if not result:
                        logger.warning("Text splitter returned empty result, using fallback")
                        return text_fixer.safe_text_split(cleaned_text)

                    return result

                except Exception as e:
                    error_msg = str(e)
                    if "Separator is not found" in error_msg or "chunk exceed" in error_msg:
                        logger.warning(f"Text splitter error caught: {error_msg}, using fallback")
                        return text_fixer.safe_text_split(text)
                    else:
                        logger.error(f"Unexpected text splitter error: {error_msg}")
                        raise e

            # Apply the patch
            RecursiveCharacterTextSplitter.split_text = safe_split_text

            logger.info("✅ LangChain RecursiveCharacterTextSplitter patched for safety")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to patch text splitter: {e}")
            return False


def apply_text_processing_fixes():
    """
    Main function to apply all text processing fixes
    """
    logger.info("🔧 Applying text processing fixes to prevent chunking errors...")

    patcher = ChunkingErrorPrevention()

    success_count = 0
    total_patches = 2

    # Patch GPT-researcher compression
    if patcher.patch_gpt_researcher_compression():
        success_count += 1

    # Patch LangChain text splitter
    if patcher.patch_langchain_text_splitter():
        success_count += 1

    if success_count == total_patches:
        logger.info("✅ All text processing fixes applied successfully!")
        logger.info("📋 Applied fixes:")
        logger.info("   • Conservative chunk sizes (800 chars max)")
        logger.info("   • Robust separator handling")
        logger.info("   • Text validation and cleaning")
        logger.info("   • Fallback splitting methods")
        logger.info("   • Error catching and graceful degradation")
        return True
    else:
        logger.warning(f"⚠️  Partial success: {success_count}/{total_patches} patches applied")
        return False


if __name__ == "__main__":
    # Test the text processing fix
    import logging

    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    fixer = TextChunkingFix()

    # Test with problematic text
    test_texts = [
        "",  # Empty text
        "a" * 10000,  # Very long text
        "Short text",  # Normal text
        "Text\n\nWith\n\nParagraphs\n\nAnd\n\nMore\n\nContent" * 100,  # Long with separators
    ]

    for i, text in enumerate(test_texts):
        print(f"\n--- Test {i + 1}: {len(text)} characters ---")
        is_valid, result = fixer.validate_text_for_processing(text)
        print(f"Valid: {is_valid}")

        if is_valid:
            chunks = fixer.safe_text_split(result)
            print(f"Chunks created: {len(chunks)}")
            for j, chunk in enumerate(chunks[:3]):  # Show first 3 chunks
                print(f"  Chunk {j + 1}: {len(chunk)} chars - {chunk[:50]}...")
        else:
            print(f"Error: {result}")
