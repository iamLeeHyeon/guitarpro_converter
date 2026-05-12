import re
from dataclasses import dataclass
from backend.parser.pdf import PageData


@dataclass
class GuitarInfo:
    tuning: str = "standard"
    capo: int = 0
    tempo: int = 120
    time_sig: tuple[int, int] = (4, 4)
    key: str = "C"


_TUNING_PATTERNS: list[tuple[str, str]] = [
    (r'drop[\s-]?d', "drop_d"),
    (r'dadgad', "dadgad"),
    (r'open[\s-]?g', "open_g"),
    (r'open[\s-]?e', "open_e"),
    (r'open[\s-]?d', "open_d"),
    (r'half[\s-]?step[\s-]?down', "half_step_down"),
]

_CAPO_RE = re.compile(r'capo\s*[:#]?\s*(\d+)', re.IGNORECASE)
_TEMPO_BPM_RE = re.compile(r'(\d{2,3})\s*bpm', re.IGNORECASE)
_TEMPO_MARK_RE = re.compile(r'♩\s*=?\s*(\d{2,3})')
_TIME_SIG_RE = re.compile(r'\b([2-9]|1[0-9])/(2|4|8|16)\b')
_KEY_RE = re.compile(r'\bkey\s+of\s+([A-G][#b]?(?:\s*(?:major|minor|maj|min))?)', re.IGNORECASE)


def extract_guitar_info(pages: list[PageData]) -> GuitarInfo:
    full_text = "\n".join(p.text for p in pages)
    lower = full_text.lower()
    info = GuitarInfo()

    # 튜닝
    for pattern, tuning_name in _TUNING_PATTERNS:
        if re.search(pattern, lower):
            info.tuning = tuning_name
            break

    # 카포
    m = _CAPO_RE.search(full_text)
    if m:
        info.capo = int(m.group(1))

    # 템포
    m = _TEMPO_BPM_RE.search(full_text)
    if m:
        info.tempo = int(m.group(1))
    else:
        m = _TEMPO_MARK_RE.search(pages[0].text if pages else "")
        if m:
            info.tempo = int(m.group(1))

    # 박자표 (첫 페이지에서 우선 탐색)
    first_text = pages[0].text if pages else ""
    m = _TIME_SIG_RE.search(first_text)
    if m:
        info.time_sig = (int(m.group(1)), int(m.group(2)))

    # 조성
    m = _KEY_RE.search(full_text)
    if m:
        info.key = m.group(1).strip()

    return info
