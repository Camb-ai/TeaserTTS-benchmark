"""
This is the second processing script, that cleans audio from background sound 
with UVR-MDX-NET, then splits it into segments using subtitles from teasers.json.
Cleaned audio and segments will be stored in "./segments/" output directory.

To run the scipt: activate python venv and install additional dependencies

    $ source ./venv/bin/activate

    $ pip install pysubs2 soundfile scipy 

To install separator with hardware support visit https://pypi.org/project/audio-separator/

    $ pip install "audio-separator[gpu]"
    or 
    $ pip install "audio-separator[cpu]"

Run the cleaning script

    $ python load_segments.py
"""
import os
import json
import shutil
import pysubs2
import soundfile as sf
from scipy.signal import resample
from audio_separator.separator import Separator


def resample_audio(audio_path, target_path, target_rate=16_000):
    audio_np, sample_rate = sf.read(audio_path)
    if audio_np.ndim > 1:
        audio_np = audio_np.mean(axis=1, dtype=audio_np.dtype)
    if sample_rate != target_rate:
        num_original_samples = len(audio_np)
        num_target_samples = int(num_original_samples * target_rate / sample_rate)
        resampled_audio = resample(audio_np, num_target_samples)
        sf.write(target_path, resampled_audio, target_rate)
    return resampled_audio


def write_segments(audio_filename, subs_filename, audio_lang, text_lang, output_dir="./output/"):
    audio, sample_rate = sf.read(audio_filename)
    print("audio", audio.shape, "@", sample_rate)
    subs = pysubs2.load(subs_filename, encoding="utf-8")
    segments_json = []
    for i, line in enumerate(subs):
        start_ms = line.start
        end_ms = line.end
        start_frame = int(start_ms / 1000 * sample_rate)
        end_frame = int(end_ms / 1000 * sample_rate)
        segment_duration = (end_ms - start_ms) / 1000
        segment_text = line.plaintext.replace("\n", " ")
        print("line", start_ms, "-", end_ms, ":", segment_text)
        
        multiple_speakers = segment_text.count("-") > 1

        if segment_duration > 1.0 and not multiple_speakers:  # this filtration was done for all baselines:
            segment = audio[start_frame:end_frame]
            segments_json.append({
                'filename': f"segment_{i}.wav",
                'start_frame': start_frame,
                'end_frame': end_frame,
                'start_ms': start_ms,
                'end_ms': end_ms,
                'audio_lang': audio_lang,
                'text_lang': text_lang,
                'text': segment_text,
            })
            sf.write(f"{output_dir}/segment_{i}.wav", segment, sample_rate)
            print(f"Segment_{i} is saved into: {output_dir}")     
    with open(f"{output_dir}/segments.json", "w", encoding="utf-8") as f:
        json.dump(segments_json, f, indent=4, ensure_ascii=False)
        print(f"JSON is saved into: {output_dir}/segments.json")
    return segments_json


if __name__ == "__main__":
    print("Cleaning data in ./data/ ...")
    with open("teasers.json", "r", encoding='utf-8') as f:
        dataset = json.load(f)

    separator = Separator(output_single_stem="Vocals")
    separator.load_model("UVR-MDX-NET-Voc_FT.onnx")

    for audio_data in dataset:
        filename = audio_data["filename"]
        audio_filename = audio_data["audio_filename"]
        subs_filename = audio_data["subs_filenames"][0]

        audio_lang = audio_data["lang_code"]
        subs_lang = audio_data["subs_lang_code"]

        input_path = f"./data/{audio_filename}"
        subs_path = f"./data/{subs_filename}"
        output_dir = f"./segments/{filename}/"
        vocals_path = output_dir + filename + ".wav"

        if not os.path.exists(vocals_path):
            print(f"Cleaning audio: {audio_filename}")
            output_files = separator.separate(input_path)

            # By default, separator creates two files:
            # [TrackName]_(Vocals)_UVR-MDX-NET-Voc_FT.wav
            # [TrackName]_(Instrumental)_UVR-MDX-NET-Voc_FT.wav

            os.makedirs(output_dir, exist_ok=True)
            for output_file in output_files:
                if "(Vocals)" in output_file:
                    shutil.move(output_file, vocals_path)
                else:
                    os.remove(output_file)
        print(f"Background is removed, saved into: {vocals_path}")
        
        segment_json = write_segments(vocals_path, subs_path, audio_lang, subs_lang, output_dir)
        print("DONE:", audio_filename, f"segments: {len(segment_json)}")
    
    print("---- FINISHED PROCESSING ----")


