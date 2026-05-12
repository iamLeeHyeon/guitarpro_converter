from dataclasses import dataclass
import fitz  # PyMuPDF


@dataclass
class PageData:
    number: int
    text: str
    words: list  # (x0, y0, x1, y1, word, block_no, line_no, word_no)


def extract_pages(pdf_path: str) -> list[PageData]:
    doc = fitz.open(pdf_path)
    if doc.is_encrypted:
        doc.close()
        raise ValueError("암호화된 PDF는 지원하지 않습니다.")
    pages = []
    for i, page in enumerate(doc):
        pages.append(PageData(
            number=i,
            text=page.get_text(),
            words=page.get_text("words"),
        ))
    doc.close()
    return pages
