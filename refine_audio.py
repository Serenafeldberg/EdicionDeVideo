#!/usr/bin/env python3
"""
remove_silences_crossfade.py

Elimina silencios de un archivo WAV y aplica crossfade entre segmentos para transiciones suaves.
"""
from pydub import AudioSegment, silence

# Parámetros fijos
input_path = "speaker/speaker00_clean.wav"
output_path = "speaker/speaker00_processed.wav"
min_silence_len = 500    # Duración mínima de silencio en ms
silence_thresh = None    # Umbral de silencio en dBFS; si es None, se calcula como audio.dBFS - 16
padding_ms = 300         # Padding extra antes y después de cada segmento en ms
crossfade_ms = 100        # Duración de fundido cruzado entre segmentos (ms)

# 1) Carga el audio
audio = AudioSegment.from_wav(input_path)

# 2) Calcula umbral si no está definido
if silence_thresh is None:
    silence_thresh = audio.dBFS - 16

# 3) Detecta rangos no silenciosos
nonsilent_ranges = silence.detect_nonsilent(
    audio,
    min_silence_len=min_silence_len,
    silence_thresh=silence_thresh,
    seek_step=1
)
nonsilent_ranges.sort(key=lambda x: x[0])

# 4) Extrae y concatena con crossfade
result = AudioSegment.empty()
for start_ms, end_ms in nonsilent_ranges:
    # Aplica padding y límites
    s = max(0, start_ms - padding_ms)
    e = min(len(audio), end_ms + padding_ms)
    chunk = audio[s:e]
    if len(result) == 0:
        result = chunk
    else:
        # Fundido cruzado para mezcla suave
        result = result.append(chunk, crossfade=crossfade_ms)

# 5) Exporta el resultado
result.export(output_path, format="wav")
print(f"Archivo sin silencios guardado con crossfade en: {output_path}")
