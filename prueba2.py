from pyannote.audio import Pipeline
from pydub import AudioSegment

# 1) Extraé tu audio (si no lo hiciste aún)
#    ffmpeg -i input.mp4 -vn -ac 1 -ar 16000 audio.wav

# 2) Carga el pipeline de diarización (requiere token HF)
pipeline = Pipeline.from_pretrained(
    "pyannote/speaker-diarization",
    use_auth_token=True
)

# 3) Diariza, forzando dos oradores
diarization = pipeline("audio.wav", min_speakers=2, max_speakers=2)

# 4) Lee el audio con pydub
audio = AudioSegment.from_wav("audio.wav")
out0 = AudioSegment.silent(duration=len(audio))
out1 = AudioSegment.silent(duration=len(audio))

# 5) Superpone sólo los turnos del segundo hablante
for turn, _, speaker in diarization.itertracks(yield_label=True):
    if speaker == "SPEAKER_00":
        start_ms = int(turn.start * 1000)
        end_ms   = int(turn.end   * 1000)
        fragment = audio[start_ms:end_ms]
        out0 = out0.overlay(fragment, position=start_ms)
    elif speaker == "SPEAKER_01":
        start_ms = int(turn.start * 1000)
        end_ms   = int(turn.end   * 1000)
        fragment = audio[start_ms:end_ms]
        out1 = out1.overlay(fragment, position=start_ms)

# 6) Exporta el WAV filtrado
out0.export("speaker/speaker00_clean.wav", format="wav")
out1.export("speaker/speaker01_clean.wav", format="wav")

# for i in range(len(outs)):
#     outs[i].export(f"speaker/speker{i}.wav", format="wav")

