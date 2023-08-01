import mimetypes
from mutagen import flac, mp3
import os

def read_flac(file):
    pic = None
    pic_type = None
    flac_file = flac.Open(file)
    try:
        pic = flac_file.pictures[0]
        pic_type = mimetypes.guess_extension(pic.mime if type(pic.mime) == str else pic.mime[0]) #left for now change later
        pic = pic.data 
    except IndexError:
        pass
    return pic, pic_type

def read_mp3(file):
    pic = None
    pic_type = None
    pic = mp3.Open(file).tags # Can swap to mutagen.id3.ID3(file)? Not sure seems same but perhaps not though tags is of type mutagen.id3.ID3
    if pic:
        for opt in pic.keys():
            if opt.startswith("APIC") or opt.startswith("PIC"):
                pic = pic.get(opt)
                pic_type = "."+pic.mime[pic.mime.find("/")+1:] # this seems more reliable than mimetypes.guess_extension(pic.mime), as "image/jpg" not detected as .jpg for some reason
                pic = pic.data
                break
            
    return pic, pic_type

def read_image_from_music(file):
    if file.endswith(".flac"):
        pic, pic_type = read_flac(file)
    elif file.endswith(".mp3"):
        pic, pic_type = read_mp3(file)

    return pic, pic_type

def image_search(root, dirs, files, recursive_depth=0):
    cover = None
    status = -1 # -1 None, 0 Any Image, 1 Front
    for file in files:
        if not (file.endswith(".jpg") or file.endswith(".jpeg") or file.endswith(".png")):
            continue
        if (file[:file.rfind(".")].lower().endswith("cover")):
            return f"{root}\\{file}"
        if (file[:file.rfind(".")].lower().endswith("front")):
            if status < 1:
                cover = file
        elif (file.endswith(".jpg") or file.endswith(".jpeg") or file.endswith(".png")):
            if status < 0:
                cover = file

    if recursive_depth > 0 or recursive_depth == -1:
        if recursive_depth == -1:
            recursive_depth = 0
        
        if (not cover or status <= 0) and len(dirs) > 0:
            for cur_dir in dirs:
                for rec_root, rec_dirs, rec_files, in os.walk(cur_dir):
                    cover = f"rec_root\\" + image_search(rec_dirs, rec_files, recursive_depth-1)
                    if cover:
                        break
                if cover:
                    break
    if cover:
        cover = f"{root}\\{cover}"
        
    return cover