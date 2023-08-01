import os
from pydub.utils import mediainfo
from pydub import AudioSegment

def MI(file_path):
    mi = mediainfo(file_path)
    try:
        return int(float(mi.get('duration'))*1000)
    except TypeError:
        return None

def AS(file_path):
    return len(AudioSegment.from_file(file_path))

def TAGS(file_path):
    mi = mediainfo(file_path)
    tags = mi.get('TAG',None)

    for key in ["duration_ms", "durationms", "duration"]:
        try:
            ret = tags[key]
            if key == "duration":
                print(f"DURATION - {file_path}")
            return ret
        except KeyError:
            pass
    
    return None           


if __name__ == "__main__":
    CONV_DIR = r"D:\Music_CONVERTED"
    ORIG_DIR = r"D:\Music"

    for root, dirs, files in os.walk(CONV_DIR):
        orig_root = root.replace(CONV_DIR, ORIG_DIR)
        for file in files[:3]:
            conv_file = root+"\\"+file
            orig_file = orig_root+"\\"+file
            if not os.path.exists(orig_file):
                orig_file = orig_file.replace(".mp3", ".flac")
                if not os.path.exists(orig_file):
                    continue

            conv = [TAGS(conv_file), MI(conv_file), AS(conv_file)]
            
            orig = [TAGS(orig_file), MI(orig_file), AS(orig_file)]

            if conv == orig:
                continue

            print(f"\n---- {root}\\{file}\nCONV: {conv}\nORIG: {orig}")