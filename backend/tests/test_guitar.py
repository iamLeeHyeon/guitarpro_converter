from backend.parser.guitar import extract_guitar_info, GuitarInfo
from backend.parser.pdf import PageData

def _make_pages(text: str) -> list[PageData]:
    return [PageData(number=0, text=text, words=[])]

def test_default_info_when_no_markers():
    pages = _make_pages("Some guitar music")
    info = extract_guitar_info(pages)
    assert info.tuning == "standard"
    assert info.capo == 0
    assert info.tempo == 120
    assert info.time_sig == (4, 4)

def test_detects_drop_d_tuning():
    pages = _make_pages("Drop D tuning\nGuitar Tab")
    info = extract_guitar_info(pages)
    assert info.tuning == "drop_d"

def test_detects_capo():
    pages = _make_pages("Capo 3\nGuitar Tab")
    info = extract_guitar_info(pages)
    assert info.capo == 3

def test_detects_tempo_bpm():
    pages = _make_pages("Tempo: 140 BPM\nGuitar")
    info = extract_guitar_info(pages)
    assert info.tempo == 140

def test_detects_time_signature():
    pages = _make_pages("3/4\nGuitar Tab")
    info = extract_guitar_info(pages)
    assert info.time_sig == (3, 4)

def test_detects_dadgad():
    pages = _make_pages("DADGAD\nGuitar")
    info = extract_guitar_info(pages)
    assert info.tuning == "dadgad"
