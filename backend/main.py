import tempfile
import os
from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask

from backend.parser.pdf import extract_pages
from backend.parser.tab import has_tab, parse_tab
from backend.parser.guitar import extract_guitar_info
from backend.converter.gp import build_song, write_gp

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

ALLOWED_FORMATS = {"gp5", "gpx", "gp"}
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/convert")
async def convert(
    file: UploadFile = File(...),
    format: str = Form(default="gp5"),
):
    if not (file.filename or "").lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="PDF 파일만 지원합니다.")
    if format not in ALLOWED_FORMATS:
        raise HTTPException(status_code=400, detail=f"지원 포맷: {ALLOWED_FORMATS}")

    pdf_bytes = await file.read(MAX_FILE_SIZE + 1)
    if len(pdf_bytes) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="파일 크기는 20MB를 초과할 수 없습니다.")

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_in:
        tmp_in.write(pdf_bytes)
        tmp_in_path = tmp_in.name

    with tempfile.NamedTemporaryFile(suffix=f".{format}", delete=False) as tmp_out:
        output_path = tmp_out.name

    try:
        pages = extract_pages(tmp_in_path)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        try:
            os.unlink(tmp_in_path)
        except OSError:
            pass

    guitar_info = extract_guitar_info(pages)

    all_measures = []
    for page in pages:
        if has_tab(page):
            all_measures.extend(parse_tab(page))

    if not all_measures:
        try:
            os.unlink(output_path)
        except OSError:
            pass
        raise HTTPException(
            status_code=422,
            detail="TAB 표기를 찾을 수 없습니다. TAB이 포함된 기타 악보 PDF를 업로드해주세요.",
        )

    try:
        song = build_song(all_measures, guitar_info)
        write_gp(song, output_path)
    except Exception:
        try:
            os.unlink(output_path)
        except OSError:
            pass
        raise

    safe_name = os.path.basename(file.filename or "output")
    safe_stem = os.path.splitext(safe_name)[0]
    download_name = f"{safe_stem}.{format}"

    def _cleanup():
        try:
            os.unlink(output_path)
        except OSError:
            pass

    return FileResponse(
        output_path,
        media_type="application/octet-stream",
        filename=download_name,
        background=BackgroundTask(_cleanup),
    )
