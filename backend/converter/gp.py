import guitarpro
from backend.parser.tab import TabNote
from backend.parser.guitar import GuitarInfo

_QUARTER_TIME = guitarpro.Duration.quarterTime  # 960

_TUNING_MAP: dict[str, list[int]] = {
    "standard":       [64, 59, 55, 50, 45, 40],
    "drop_d":         [64, 59, 55, 50, 45, 38],
    "open_g":         [62, 59, 55, 50, 43, 38],
    "dadgad":         [62, 57, 55, 50, 45, 38],
    "open_e":         [64, 59, 56, 52, 47, 40],
    "open_d":         [62, 57, 54, 50, 45, 38],
    "half_step_down": [63, 58, 54, 49, 44, 39],
}

# (틱, 음표값) 내림차순
_DURATION_TABLE = [(3840, 1), (1920, 2), (960, 4), (480, 8), (240, 16), (120, 32)]


def _nearest_duration_value(ticks: int) -> int:
    for tick_val, dur_val in _DURATION_TABLE:
        if ticks >= tick_val * 0.75:
            return dur_val
    return 16


def build_song(all_measures: list[list[TabNote]], info: GuitarInfo) -> guitarpro.Song:
    song = guitarpro.Song()
    song.tempo = info.tempo

    tuning = _TUNING_MAP.get(info.tuning, _TUNING_MAP["standard"])
    num, den = info.time_sig
    ticks_per_measure = num * (_QUARTER_TIME * 4 // den)

    # 기본 Song에는 track 1개, measure 1개가 있으므로 재활용
    track = song.tracks[0]
    track.name = "Guitar"
    track.strings = [guitarpro.GuitarString(i + 1, v) for i, v in enumerate(tuning)]
    track.channel.instrument = 25  # Acoustic Guitar (steel)

    # 기본 MeasureHeader/Measure 제거 후 새로 구성
    song.measureHeaders.clear()
    track.measures.clear()

    current_start = _QUARTER_TIME
    for measure_notes in all_measures:
        header = guitarpro.MeasureHeader()
        header.number = len(song.measureHeaders) + 1
        header.start = current_start
        header.timeSignature.numerator = num
        header.timeSignature.denominator = guitarpro.Duration(value=den)
        song.measureHeaders.append(header)

        measure = guitarpro.Measure(track, header)
        voice = measure.voices[0]
        _fill_voice(voice, measure_notes, ticks_per_measure, current_start)
        # GP5는 voice 2개를 모두 씀 — voice[1]에 whole rest 추가
        _fill_rest_voice(measure.voices[1], current_start)
        track.measures.append(measure)

        current_start += ticks_per_measure

    return song


def _fill_voice(
    voice: guitarpro.Voice,
    notes: list[TabNote],
    ticks_per_measure: int,
    measure_start: int,
) -> None:
    if not notes:
        beat = guitarpro.Beat(voice)
        beat.start = measure_start
        beat.duration = guitarpro.Duration(value=1)
        beat.status = guitarpro.BeatStatus.rest
        voice.beats.append(beat)
        return

    unique_cols = sorted(set(n.col for n in notes))
    n_beats = len(unique_cols)
    ticks_per_beat = max(ticks_per_measure // n_beats, 120)
    dur_value = _nearest_duration_value(ticks_per_beat)

    for beat_idx, col in enumerate(unique_cols):
        beat = guitarpro.Beat(voice)
        beat.start = measure_start + beat_idx * ticks_per_beat
        beat.status = guitarpro.BeatStatus.normal
        beat.duration = guitarpro.Duration(value=dur_value)

        for tab_note in (n for n in notes if n.col == col):
            # Note 첫 인자는 부모 beat, string은 1-indexed (1=high e, 6=low E)
            gp_note = guitarpro.Note(
                beat,
                string=tab_note.string_idx + 1,
                value=tab_note.fret,
                type=guitarpro.NoteType.normal,
            )
            gp_note.velocity = guitarpro.Velocities.forte
            _apply_technique(gp_note, tab_note.technique, tab_note.palm_mute)
            beat.notes.append(gp_note)

        voice.beats.append(beat)


def _fill_rest_voice(voice: guitarpro.Voice, measure_start: int) -> None:
    """GP5 두 번째 voice에 whole rest 채우기."""
    beat = guitarpro.Beat(voice)
    beat.start = measure_start
    beat.status = guitarpro.BeatStatus.rest
    beat.duration = guitarpro.Duration(value=1)
    voice.beats.append(beat)


def _apply_technique(note: guitarpro.Note, technique: str, palm_mute: bool) -> None:
    if palm_mute:
        note.effect.palmMute = True
    if not technique:
        return
    if technique in ('h', 'p'):
        # GP 형식에서 hammer-on과 pull-off는 같은 플래그(hammer)로 표현됨
        note.effect.hammer = True
    elif technique == '/':
        note.effect.slides = [guitarpro.SlideType.shiftSlideTo]
    elif technique == '\\':
        note.effect.slides = [guitarpro.SlideType.legatoSlideTo]
    elif technique in ('b', 'B'):
        note.effect.bend = guitarpro.BendEffect(
            type=guitarpro.BendType.bend,
            value=100,
            points=[
                guitarpro.BendPoint(0, 0),
                guitarpro.BendPoint(6, 100),
                guitarpro.BendPoint(12, 100),
            ],
        )
    elif technique == '~':
        note.effect.vibrato = True
    elif technique in ('T', 't'):
        # tapping: hammer-on으로 근사
        note.effect.hammer = True


def write_gp(song: guitarpro.Song, output_path: str) -> None:
    """GP 파일 저장. 확장자에 따라 포맷 자동 결정 (.gp5 / .gpx / .gp)."""
    guitarpro.write(song, output_path)
