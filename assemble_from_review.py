#!/usr/bin/env python3
"""
assemble_from_keepids.py

Concatena fragmentos de audio seleccionados (por sus IDs) en un nuevo WAV y
guarda los timestamps originales en `keep_ranges.txt`.

Uso:
  - Ejecuta primero `segment_and_review.py` para generar `segments/metadata.json`.
  - Edita la lista `KEEP_IDS` abajo con los IDs de los fragments que quieres conservar.
  - Luego ejecuta este script:
      python assemble_from_keepids.py
Salida:
  - `speaker/speaker00_selected.wav` conteniendo sólo los fragments elegidos.
  - `speaker/keep_ranges.txt` con los rangos (start end) en segundos para cortar el MP4.
"""

import os
import json
from pydub import AudioSegment

# ------------------------------
# Define manualmente aquí los IDs de los fragments a conservar.
# Por ejemplo: KEEP_IDS = [0, 2, 3, 5]
KEEP_IDS = [2, 4, 5, 7, 8, 9, 10, 11, 13, 14, 15]  # ← Sustituye con los IDs que hayas elegido
# ------------------------------

segments_dir    = "segments"
metadata_path   = os.path.join(segments_dir, "metadata.json")
original_audio  = "speaker/speaker00_clean.wav"
output_audio    = "speaker/speaker00_selected.wav"
keep_ranges_txt = "speaker/keep_ranges.txt"

# Parámetro opcional de crossfade (en ms) al unir fragments
CROSSFADE_MS = 50

# 1) Carga metadata.json para obtener lista completa de segments
with open(metadata_path, "r", encoding="utf-8") as f:
    metadata = json.load(f)  # lista de dicts: id, file, start, end, transcript

# 2) Filtra sólo los segments cuyos IDs estén en KEEP_IDS
kept_segments = [seg for seg in metadata if seg["id"] in KEEP_IDS]
# Ordena por timestamp de inicio para mantener el orden cronológico
kept_segments.sort(key=lambda seg: seg["start"])

if not kept_segments:
    print("⚠️ La lista KEEP_IDS está vacía o no coincide con ningún ID.")
    exit(0)

# 3) Extrae los timestamps originales y los escribe en keep_ranges.txt
os.makedirs(os.path.dirname(keep_ranges_txt), exist_ok=True)
with open(keep_ranges_txt, "w", encoding="utf-8") as kr:
    for seg in kept_segments:
        # 'start' y 'end' están en segundos con tres decimales
        kr.write(f"{seg['start']:.3f} {seg['end']:.3f}\n")
print(f"→ keep_ranges.txt generado con {len(kept_segments)} rangos: {keep_ranges_txt}")

# 4) Carga el audio original (el usado para segmentar)
audio = AudioSegment.from_wav(original_audio)

# 5) Concatena los fragments seleccionados en un solo AudioSegment
result = AudioSegment.empty()
for idx, seg in enumerate(kept_segments):
    start_ms = int(seg["start"] * 1000)
    end_ms   = int(seg["end"]   * 1000)
    chunk = audio[start_ms:end_ms]
    if idx == 0 or CROSSFADE_MS == 0:
        result = result + chunk
    else:
        result = result.append(chunk, crossfade=CROSSFADE_MS)

# 6) Asegura que existe la carpeta de salida y exporta el nuevo WAV
os.makedirs(os.path.dirname(output_audio), exist_ok=True)
result.export(output_audio, format="wav")
print(f"→ WAV concatenado generado: {output_audio}")
