from backend.parser.tab import has_tab, parse_tab, TabNote
from backend.parser.pdf import PageData

def _make_page(text: str) -> PageData:
    return PageData(number=0, text=text, words=[])

TAB_TEXT = """\
e|---5---3---7---|
B|---5---3---8---|
G|---6---4---9---|
D|---7---5--10---|
A|---------------|
E|---------------|
"""

NOTATION_ONLY = """\
Some sheet music without tablature.
Notes written in standard notation only.
"""

def test_has_tab_detects_standard_tab():
    page = _make_page(TAB_TEXT)
    assert has_tab(page) is True

def test_has_tab_returns_false_for_notation_only():
    page = _make_page(NOTATION_ONLY)
    assert has_tab(page) is False

def test_parse_tab_returns_tab_notes():
    page = _make_page(TAB_TEXT)
    measures = parse_tab(page)
    assert len(measures) > 0
    assert all(isinstance(n, TabNote) for measure in measures for n in measure)

def test_parse_tab_extracts_correct_fret():
    page = _make_page(TAB_TEXT)
    measures = parse_tab(page)
    all_notes = [n for m in measures for n in m]
    frets = {n.fret for n in all_notes}
    assert 5 in frets
    assert 3 in frets

def test_parse_tab_assigns_string_index():
    page = _make_page(TAB_TEXT)
    measures = parse_tab(page)
    all_notes = [n for m in measures for n in m]
    string_indices = {n.string_idx for n in all_notes}
    # e=0, B=1, G=2, D=3
    assert 0 in string_indices
    assert 1 in string_indices

def test_parse_tab_detects_hammer_on():
    text = "e|---5h7---|\nB|---------|\nG|---------|\nD|---------|\nA|---------|\nE|---------|"
    page = _make_page(text)
    measures = parse_tab(page)
    all_notes = [n for m in measures for n in m]
    hammers = [n for n in all_notes if n.technique == 'h']
    assert len(hammers) >= 1

def test_parse_tab_detects_slide():
    text = "e|---5/7---|\nB|---------|\nG|---------|\nD|---------|\nA|---------|\nE|---------|"
    page = _make_page(text)
    measures = parse_tab(page)
    all_notes = [n for m in measures for n in m]
    slides = [n for n in all_notes if n.technique == '/']
    assert len(slides) >= 1
