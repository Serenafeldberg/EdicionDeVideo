#!/usr/bin/env python3
"""
segment_and_review.py

Segmenta un WAV en fragmentos de voz, exporta cada fragmento con padding,
transcribe cada uno con Whisper y genera un JSON para revisión manual.
El usuario podrá escuchar segments/segment_###.wav y decidir cuáles conservar.
"""
import os
import json
from pydub import AudioSegment, silence
import whisper

# Parámetros fijos
audio_path     = "speaker/speaker00_clean.wav"
output_dir     = "segments"
padding_ms     = 150        # ms extra antes/después de cada segmento
min_silence_len= 500        # ms mínimo de silencio para separar
silence_thresh = None       # si None, se usará audio.dBFS - 16

# Asegura directorio
os.makedirs(output_dir, exist_ok=True)

# 1) Carga el audio
audio = AudioSegment.from_wav(audio_path)
if silence_thresh is None:
    silence_thresh = audio.dBFS - 16

# 2) Detecta rangos de voz
nonsilent = silence.detect_nonsilent(
    audio,
    min_silence_len=min_silence_len,
    silence_thresh=silence_thresh,
    seek_step=1
)
nonsilent.sort(key=lambda x: x[0])

# 3) Carga modelo Whisper
model = whisper.load_model("base")

metadata = []

# 4) Extrae, exporta y transcribe cada fragmento
for idx, (start_ms, end_ms) in enumerate(nonsilent):
    s = max(0, start_ms - padding_ms)
    e = min(len(audio), end_ms + padding_ms)
    chunk = audio[s:e]
    fname = f"segment_{idx:03d}.wav"
    path = os.path.join(output_dir, fname)
    chunk.export(path, format="wav")

    # Transcribe con Whisper (solo texto)
    result = model.transcribe(path)
    text = " ".join(segment['text'] for segment in result['segments'])

    metadata.append({
        "id": idx,
        "file": fname,
        "start": round(s / 1000, 3),
        "end":   round(e / 1000, 3),
        "transcript": text.strip()
    })
    print(f"Generated {fname}: {text.strip()[:60]}...")

# 5) Guarda metadata para revisión manual
meta_path = os.path.join(output_dir, "metadata.json")
with open(meta_path, "w") as f:
    json.dump(metadata, f, ensure_ascii=False, indent=2)

print(f"""
Segmentación completa: {len(metadata)} fragments.
Revisa el directorio '{output_dir}', escucha cada WAV y edita 'keep_ids' en el JSON a continuación.
""")

# 6) Inicializa el campo de revisión (IDs a conservar)
keep = []  # ej. [0, 2, 3, 5]
review = {
    "segments": metadata,
    "keep_ids": keep
}
review_path = os.path.join(output_dir, "review.json")
with open(review_path, "w") as f:
    json.dump(review, f, ensure_ascii=False, indent=2)

print(f"Archivo de revisión generado: {review_path}")
