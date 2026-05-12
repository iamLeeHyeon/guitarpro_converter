import re
from dataclasses import dataclass, field
from backend.parser.pdf import PageData

# 기타 줄 레이블 → string_idx (0=e high, 5=E low)
_STRING_LABELS = {'e': 0, 'B': 1, 'G': 2, 'D': 3, 'A': 4, 'E': 5}
_MIN_STRINGS = 4  # 최소 몇 줄이 있어야 TAB으로 인정

# TAB 라인 패턴: "e|---5---3---|" 형태
_TAB_LINE_RE = re.compile(r'^([eBGDAE])\|([-0-9hpbBr/\\~^TtPM\s]+)\|?\s*$')

# 주법 기호 패턴: 선택적 기호 + 숫자 + 선택적 기호
_NOTE_RE = re.compile(r'([hpbBr/\\~^T]?)(\d+)([hpbBr/\\~^T]?)')

# 팜뮤트 블록 패턴
_PALM_MUTE_RE = re.compile(r'PM[-]+')


@dataclass
class TabNote:
    string_idx: int   # 0=e(high), 5=E(low)
    fret: int
    col: int          # 줄 내 문자 컬럼 (타이밍 프록시)
    technique: str = ""
    palm_mute: bool = False


def has_tab(page: PageData) -> bool:
    """페이지에 기타 TAB 표기가 있는지 감지."""
    lines = page.text.splitlines()
    matched = sum(1 for line in lines if _TAB_LINE_RE.match(line.strip()))
    return matched >= _MIN_STRINGS


def parse_tab(page: PageData) -> list[list[TabNote]]:
    """TAB 텍스트에서 마디별 TabNote 리스트를 추출."""
    lines = page.text.splitlines()
    measures: list[list[TabNote]] = []

    i = 0
    while i < len(lines):
        block = _find_tab_block(lines, i)
        if block:
            measures.extend(_parse_block(block))
            i += len(block)
        else:
            i += 1

    return measures


def _find_tab_block(lines: list[str], start: int) -> list[str] | None:
    """연속된 TAB 줄 블록(최소 4줄)을 찾아 반환."""
    candidate = []
    for line in lines[start:start + 8]:
        if _TAB_LINE_RE.match(line.strip()):
            candidate.append(line.strip())
        elif candidate:
            break
    if len(candidate) >= _MIN_STRINGS:
        return candidate
    return None


def _parse_block(block: list[str]) -> list[list[TabNote]]:
    """TAB 블록에서 마디 구분(|)으로 나눠 마디별 TabNote 리스트 반환."""
    string_measures: list[tuple[int, list[str]]] = []

    for line in block:
        m = _TAB_LINE_RE.match(line)
        if not m:
            continue
        label, content = m.group(1), m.group(2)
        string_idx = _STRING_LABELS.get(label)
        if string_idx is None:
            continue
        bar_segments = content.split('|')
        string_measures.append((string_idx, bar_segments))

    if not string_measures:
        return []

    num_measures = max(len(segs) for _, segs in string_measures)
    result: list[list[TabNote]] = [[] for _ in range(num_measures)]

    for string_idx, segments in string_measures:
        for measure_idx, segment in enumerate(segments):
            if measure_idx >= num_measures:
                break
            is_palm_muted = bool(_PALM_MUTE_RE.search(segment))
            for match in _NOTE_RE.finditer(segment):
                pre_tech = match.group(1)
                fret = int(match.group(2))
                post_tech = match.group(3)
                technique = pre_tech or post_tech
                result[measure_idx].append(TabNote(
                    string_idx=string_idx,
                    fret=fret,
                    col=match.start(),
                    technique=technique,
                    palm_mute=is_palm_muted,
                ))

    # 빈 마디 제거
    return [m for m in result if m]
