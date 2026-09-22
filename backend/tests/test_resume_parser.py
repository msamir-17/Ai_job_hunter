import io
import docx
import pypdf
import pytest

from app.services.resume_parser import MAX_FILE_SIZE_BYTES, parse_resume_file


def create_sample_pdf_bytes(text_content: str = "Sample Resume Text") -> bytes:
    """Helper to generate a valid PDF byte buffer containing extractable text."""
    stream_content = f"BT /F1 12 Tf 100 700 Td ({text_content}) Tj ET".encode("latin-1")
    stream_len = len(stream_content)
    pdf_structure = (
        b"%PDF-1.4\n"
        b"1 0 obj <</Type /Catalog /Pages 2 0 R>> endobj\n"
        b"2 0 obj <</Type /Pages /Kids [3 0 R] /Count 1>> endobj\n"
        b"3 0 obj <</Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources <</Font <</F1 4 0 R>>>> /Contents 5 0 R>> endobj\n"
        b"4 0 obj <</Type /Font /Subtype /Type1 /BaseFont /Helvetica>> endobj\n"
        b"5 0 obj <</Length " + str(stream_len).encode("latin-1") + b">> stream\n"
        + stream_content + b"\nendstream\nendobj\n"
        b"xref\n0 6\n0000000000 65535 f\n"
        b"trailer <</Size 6 /Root 1 0 R>>\n"
        b"startxref\n10\n%%EOF"
    )
    return pdf_structure


def create_sample_docx_bytes(paragraphs: list[str] = None) -> bytes:
    """Helper to generate a valid DOCX byte buffer in memory."""
    if paragraphs is None:
        paragraphs = ["Jane Doe", "Software Engineer", "Skills: Python, FastAPI"]
    doc = docx.Document()
    for p in paragraphs:
        doc.add_paragraph(p)
    buffer = io.BytesIO()
    doc.save(buffer)
    return buffer.getvalue()


class TestResumeParserService:
    def test_parse_valid_pdf(self):
        pdf_bytes = create_sample_pdf_bytes("John Doe Resume")
        text = parse_resume_file("resume.pdf", pdf_bytes)
        assert "John Doe Resume" in text

    def test_parse_valid_docx(self):
        docx_bytes = create_sample_docx_bytes(["Jane Doe", "AI Engineer"])
        text = parse_resume_file("resume.docx", docx_bytes)
        assert "Jane Doe" in text
        assert "AI Engineer" in text

    def test_parse_empty_file_bytes(self):
        with pytest.raises(ValueError, match="Uploaded file is empty"):
            parse_resume_file("empty.pdf", b"")

    def test_parse_file_exceeding_max_size(self):
        large_content = b"a" * (MAX_FILE_SIZE_BYTES + 1)
        with pytest.raises(ValueError, match="exceeds maximum allowed limit of 5 MB"):
            parse_resume_file("large.pdf", large_content)

    def test_parse_unsupported_file_extension(self):
        with pytest.raises(ValueError, match="Unsupported file format"):
            parse_resume_file("resume.txt", b"plain text content")

    def test_parse_corrupt_pdf(self):
        with pytest.raises(ValueError, match="Malformed or.*PDF document"):
            parse_resume_file("corrupt.pdf", b"%PDF-1.4 invalid binary content")

    def test_parse_corrupt_docx(self):
        with pytest.raises(ValueError, match="Malformed or unreadable DOCX document"):
            parse_resume_file("corrupt.docx", b"PK\x03\x04 invalid zip header content")

    def test_parse_empty_docx_text(self):
        empty_docx_bytes = create_sample_docx_bytes([])
        with pytest.raises(ValueError, match="contains no readable text"):
            parse_resume_file("empty.docx", empty_docx_bytes)
