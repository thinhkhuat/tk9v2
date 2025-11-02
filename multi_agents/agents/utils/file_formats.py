import os
import urllib
import uuid

import aiofiles
import mistune


async def write_to_file(filename: str, text: str) -> None:
    """Asynchronously write text to a file in UTF-8 encoding.

    Args:
        filename (str): The filename to write to.
        text (str): The text to write.
    """
    # Convert text to UTF-8, replacing any problematic characters
    text_utf8 = text.encode("utf-8", errors="replace").decode("utf-8")

    async with aiofiles.open(filename, "w", encoding="utf-8") as file:
        await file.write(text_utf8)


async def write_text_to_md(text: str, path: str) -> str:
    """Writes text to a Markdown file and returns the file path.

    Args:
        text (str): Text to write to the Markdown file.

    Returns:
        str: The file path of the generated Markdown file.
    """
    task = uuid.uuid4().hex
    file_path = f"{path}/{task}.md"
    await write_to_file(file_path, text)
    print(f"Report written to {file_path}")
    return file_path


async def write_md_to_pdf(text: str, path: str) -> str:
    """Converts Markdown text to a PDF file using Pandoc and returns the file path.

    Args:
        text (str): Markdown text to convert.

    Returns:
        str: The encoded file path of the generated PDF.
    """
    import subprocess
    import tempfile

    task = uuid.uuid4().hex
    file_path = f"{path}/{task}.pdf"

    try:
        # Create a temporary markdown file
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False, encoding="utf-8"
        ) as temp_md:
            temp_md.write(text)
            temp_md_path = temp_md.name

        # Use Pandoc to convert markdown to PDF
        # Check if pandoc is available
        try:
            subprocess.run(["pandoc", "--version"], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("Pandoc is not installed. Please install it with: brew install pandoc")
            return ""

        # Try different PDF generation methods in order of preference
        pdf_engines = [
            # Method 1: Try with XeLaTeX (best quality, requires LaTeX)
            [
                "pandoc",
                temp_md_path,
                "-o",
                file_path,
                "--pdf-engine=xelatex",
                "-V",
                "geometry:margin=1in",
            ],
            # Method 2: Try with pdflatex (good quality, requires LaTeX)
            ["pandoc", temp_md_path, "-o", file_path, "--pdf-engine=pdflatex"],
            # Method 3: Basic pandoc (uses default engine)
            ["pandoc", temp_md_path, "-o", file_path],
        ]

        success = False
        last_error = ""

        for i, pandoc_cmd in enumerate(pdf_engines):
            result = subprocess.run(pandoc_cmd, capture_output=True, text=True)

            if result.returncode == 0:
                success = True
                if i > 0:
                    print(f"PDF generated using fallback method {i+1}")
                break
            else:
                last_error = result.stderr
                if i == 0:
                    print("XeLaTeX not available, trying pdflatex...")
                elif i == 1:
                    print("pdflatex not available, trying basic pandoc...")

        if not success:
            print(f"PDF generation failed. Error: {last_error}")
            print("PDF generation requires LaTeX. To install:")
            print("  brew install --cask basictex")
            print('  (then restart terminal and run: eval "$(/usr/libexec/path_helper)")')
            print("Continuing without PDF output (DOCX and Markdown will still be generated)...")
            return ""

        # Clean up temp file
        os.unlink(temp_md_path)

        print(f"Report written to {file_path}")
    except Exception as e:
        print(f"Error in converting Markdown to PDF: {e}")
        return ""

    encoded_file_path = urllib.parse.quote(file_path)
    return encoded_file_path


async def write_md_to_word(text: str, path: str) -> str:
    """Converts Markdown text to a DOCX file and returns the file path.

    Args:
        text (str): Markdown text to convert.

    Returns:
        str: The encoded file path of the generated DOCX.
    """
    task = uuid.uuid4().hex
    file_path = f"{path}/{task}.docx"

    try:
        from docx import Document
        from htmldocx import HtmlToDocx

        # Convert report markdown to HTML
        html = mistune.html(text)
        # Create a document object
        doc = Document()
        # Convert the html generated from the report to document format
        HtmlToDocx().add_html_to_document(html, doc)

        # Saving the docx document to file_path
        doc.save(file_path)

        print(f"Report written to {file_path}")

        encoded_file_path = urllib.parse.quote(file_path)
        return encoded_file_path

    except Exception as e:
        print(f"Error in converting Markdown to DOCX: {e}")
        return ""
