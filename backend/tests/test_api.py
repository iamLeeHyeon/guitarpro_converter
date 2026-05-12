import tempfile, os
import fitz
import pytest
from httpx import AsyncClient, ASGITransport
from backend.main import app

def _make_tab_pdf() -> bytes:
    """TAB이 있는 테스트용 PDF 바이트 반환."""
    tab_text = (
        "e|---5---3---7---|\n"
        "B|---5---3---8---|\n"
        "G|---6---4---9---|\n"
        "D|---7---5--10---|\n"
        "A|---------------|\n"
        "E|---------------|\n"
    )
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 100), tab_text, fontsize=10)
    path = tempfile.mktemp(suffix=".pdf")
    doc.save(path)
    doc.close()
    with open(path, "rb") as f:
        data = f.read()
    os.unlink(path)
    return data

@pytest.mark.asyncio
async def test_convert_returns_gp5():
    pdf_bytes = _make_tab_pdf()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/convert",
            files={"file": ("test.pdf", pdf_bytes, "application/pdf")},
            data={"format": "gp5"},
        )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/octet-stream"

@pytest.mark.asyncio
async def test_convert_rejects_non_pdf():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/convert",
            files={"file": ("test.txt", b"not a pdf", "text/plain")},
            data={"format": "gp5"},
        )
    assert response.status_code == 400

@pytest.mark.asyncio
async def test_health():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")
    assert response.status_code == 200
