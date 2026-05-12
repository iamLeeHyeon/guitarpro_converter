import tempfile, os
import guitarpro
import pytest
from backend.parser.tab import TabNote
from backend.parser.guitar import GuitarInfo
from backend.converter.gp import build_song, write_gp


def _simple_measure() -> list[TabNote]:
    return [
        TabNote(string_idx=0, fret=5, col=3),
        TabNote(string_idx=1, fret=5, col=3),
        TabNote(string_idx=0, fret=7, col=7),
    ]


def test_build_song_returns_guitarpro_song():
    song = build_song([_simple_measure()], GuitarInfo())
    assert isinstance(song, guitarpro.Song)


def test_build_song_has_one_track():
    song = build_song([_simple_measure()], GuitarInfo())
    assert len(song.tracks) == 1


def test_build_song_measure_count_matches():
    measures = [_simple_measure(), _simple_measure()]
    song = build_song(measures, GuitarInfo())
    assert len(song.tracks[0].measures) == 2


def test_build_song_tempo():
    info = GuitarInfo(tempo=160)
    song = build_song([_simple_measure()], info)
    assert song.tempo == 160


def test_build_song_notes_present():
    song = build_song([_simple_measure()], GuitarInfo())
    beats = song.tracks[0].measures[0].voices[0].beats
    all_notes = [n for b in beats for n in b.notes]
    frets = {n.value for n in all_notes}
    assert 5 in frets
    assert 7 in frets


def test_write_gp_produces_valid_file():
    song = build_song([_simple_measure()], GuitarInfo())
    path = tempfile.mktemp(suffix=".gp5")
    write_gp(song, path)
    assert os.path.exists(path)
    loaded = guitarpro.parse(path)
    assert loaded.tempo == song.tempo
    os.unlink(path)


def test_hammer_on_effect():
    notes = [TabNote(string_idx=0, fret=5, col=0, technique='h')]
    song = build_song([notes], GuitarInfo())
    gp_note = song.tracks[0].measures[0].voices[0].beats[0].notes[0]
    assert gp_note.effect.hammer is True


def test_pull_off_effect():
    # GP 형식에서 pull-off는 hammer 플래그로 표현됨
    notes = [TabNote(string_idx=0, fret=7, col=0, technique='p')]
    song = build_song([notes], GuitarInfo())
    gp_note = song.tracks[0].measures[0].voices[0].beats[0].notes[0]
    assert gp_note.effect.hammer is True


def test_drop_d_tuning_changes_low_e():
    info = GuitarInfo(tuning="drop_d")
    song = build_song([_simple_measure()], info)
    low_e = song.tracks[0].strings[-1]
    assert low_e.value == 38
