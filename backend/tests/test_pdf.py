import tempfile
import fitz
import pytest
from backend.parser.pdf import extract_pages, PageData

def _make_pdf(text: str) -> str:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 100), text, fontsize=12)
    path = tempfile.mktemp(suffix=".pdf")
    doc.save(path)
    doc.close()
    return path

def test_extract_pages_returns_one_page():
    path = _make_pdf("Hello Guitar")
    pages = extract_pages(path)
    assert len(pages) == 1

def test_page_data_has_text():
    path = _make_pdf("Guitar Tab Here")
    pages = extract_pages(path)
    assert "Guitar" in pages[0].text

def test_page_data_has_words_with_positions():
    path = _make_pdf("Test")
    pages = extract_pages(path)
    # words: list of (x0, y0, x1, y1, word, block_no, line_no, word_no)
    assert len(pages[0].words) > 0
    assert len(pages[0].words[0]) == 8

def test_encrypted_pdf_raises():
    import os
    path = tempfile.mktemp(suffix=".pdf")
    doc = fitz.open()
    doc.new_page()
    doc.save(path, encryption=fitz.PDF_ENCRYPT_AES_256, user_pw="pw")
    doc.close()
    with pytest.raises(ValueError, match="암호화"):
        extract_pages(path)
