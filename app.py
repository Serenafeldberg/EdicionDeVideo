# app.py
# Streamlit app to allow segment selection from uploaded MP4 and return edited MP4

import os
import subprocess
from pydub import AudioSegment, silence
import streamlit as st

st.set_page_config(page_title="Video Segment Selector", layout="wide")

# Directories
WORK_DIR = "working"
UPLOAD_DIR = os.path.join(WORK_DIR, "uploads")
SEGMENTS_DIR = os.path.join(WORK_DIR, "segments")
OUTPUT_DIR = os.path.join(WORK_DIR, "output")

for d in [UPLOAD_DIR, SEGMENTS_DIR, OUTPUT_DIR]:
    os.makedirs(d, exist_ok=True)

st.title("🎬 Video Segment Selector")
st.write("Sube un video MP4, selecciona los segmentos de audio que deseas conservar y descarga el video editado.")

# Step 1: Upload MP4
uploaded_file = st.file_uploader("1. Sube un archivo MP4", type=["mp4"], key="upload")
if uploaded_file:
    # Save upload to disk
    input_path = os.path.join(UPLOAD_DIR, uploaded_file.name)
    with open(input_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    st.success(f"Archivo guardado: {uploaded_file.name}")

    # Extract audio
    audio_path = os.path.join(UPLOAD_DIR, os.path.splitext(uploaded_file.name)[0] + ".wav")
    if not os.path.exists(audio_path):
        subprocess.run([
            "ffmpeg", "-y", "-i", input_path, "-vn", "-ac", "1", "-ar", "16000", audio_path
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    st.info("Audio extraído.")

    # Step 2: Segment audio
    audio = AudioSegment.from_wav(audio_path)
    silence_thresh = audio.dBFS - 16
    nonsilent = silence.detect_nonsilent(
        audio,
        min_silence_len=300,
        silence_thresh=silence_thresh,
        seek_step=1
    )
    nonsilent.sort(key=lambda x: x[0]) 
    
    # Clear previous segments
    for f_name in os.listdir(SEGMENTS_DIR):
        os.remove(os.path.join(SEGMENTS_DIR, f_name))

    st.write("## 2. Revisa y selecciona segmentos de video")
    selections = []
    # for idx, (start_ms, end_ms) in enumerate(nonsilent):
    #     # Apply padding
    #     s = max(0, start_ms - 150)
    #     e = min(len(audio), end_ms + 150)
    #     start_s = s / 1000
    #     end_s = e / 1000
    #     duration = end_s - start_s

    #     clip_path = os.path.join(SEGMENTS_DIR, f"segment_{idx:03d}.mp4")
    #     if not os.path.exists(clip_path):
    #         subprocess.run([
    #             "ffmpeg", "-y", "-ss", str(start_s), "-i", input_path,
    #             "-t", str(duration), "-c:v", "libx264", "-c:a", "aac", "-b:a", "128k", clip_path
    #         ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    #     # Display video and checkbox
    #     st.write(f"- Segmento {idx}: {start_s:.3f}s → {end_s:.3f}s")
    #     # with open(clip_path, "rb") as ca:
    #     #     st.video(ca.read(), format="video/mp4")
    #     import base64

    #     with open(clip_path, "rb") as vid_file:
    #         video_bytes = vid_file.read()
    #         b64 = base64.b64encode(video_bytes).decode()
    #         video_html = f"""
    #         <video width="250" controls>
    #             <source src="data:video/mp4;base64,{b64}" type="video/mp4">
    #             Tu navegador no soporta el video.
    #         </video>
    #         """
    #         st.markdown(video_html, unsafe_allow_html=True)

    #     keep = st.checkbox("Conservar este segmento", key=f"keep_{idx}")
    #     if keep:
    #         selections.append((idx, start_s, end_s))
    for idx, (start_ms, end_ms) in enumerate(nonsilent):
        # Apply padding
        s = max(0, start_ms - 150)
        e = min(len(audio), end_ms + 150)
        chunk = audio[s:e]
        chunk_path = os.path.join(SEGMENTS_DIR, f"segment_{idx:03d}.wav")
        chunk.export(chunk_path, format="wav")
        # Display segment info and audio player
        st.write(f"- Segmento {idx}: {s/1000:.3f}s → {e/1000:.3f}s")
        with open(chunk_path, "rb") as ca:
            st.audio(ca.read(), format="audio/wav")
        keep = st.checkbox("Conservar este segmento", key=f"keep_{idx}")
        if keep:
            selections.append((idx, s/1000, e/1000))


    # When user finishes selecting
    if st.button("✅ Generar video editado"):
        if not selections:
            st.warning("No seleccionaste ningún segmento.")
        else:
            # Generate keep_ranges.txt
            keep_ranges_path = os.path.join(OUTPUT_DIR, "keep_ranges.txt")
            with open(keep_ranges_path, "w") as kr:
                for idx, start_s, end_s in selections:
                    kr.write(f"{start_s:.3f} {end_s:.3f}\n")
            st.success(f"keep_ranges.txt generado con {len(selections)} rangos.")

            # Step 3: Cut video by ranges and collect segment filenames
            segment_files = []
            for i, (_idx, start_s, end_s) in enumerate(selections):
                duration = end_s - start_s
                seg_name = f"clip_{i:03d}.mp4"
                seg_out = os.path.join(OUTPUT_DIR, seg_name)
                subprocess.run([
                    "ffmpeg", "-y", "-ss", f"{start_s}", "-i", input_path,
                    "-t", f"{duration}", "-c:v", "libx264", "-c:a", "aac", "-b:a", "128k", seg_out
                ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                segment_files.append(seg_name)

            # Create concat list file inside OUTPUT_DIR using only filenames
            list_path = os.path.join(OUTPUT_DIR, "concat_list.txt")
            with open(list_path, "w") as lf:
                for seg_name in segment_files:
                    lf.write(f"file '{seg_name}'\n")

                        # Final concatenate using ffmpeg without changing cwd
            final_name = f"edited_{uploaded_file.name}"
            final_out = os.path.join(OUTPUT_DIR, final_name)
            subprocess.run([
                "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", list_path,
                "-c", "copy", final_out
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            # Check and display final video
            if os.path.exists(final_out):
                st.success(f"Video editado generado: {final_name}")
                with open(final_out, 'rb') as vid_file:
                    video_bytes = vid_file.read()
                st.video(video_bytes)
                st.download_button(
                    label="Descargar video editado",
                    data=video_bytes,
                    file_name=final_name,
                    mime="video/mp4"
                )
            else:
                st.error(f"Error: no se creó el archivo editado {final_out}")
