import mimetypes
import os
from mutagen import mp3

import tag_utils

def read_flac(tags:tag_utils.tags):
    pic = None
    pic_type = None
    flac_file = tags.file_thing
    try:
        pic = flac_file.pictures[0]
        pic_type = mimetypes.guess_extension(pic.mime if type(pic.mime) == str else pic.mime[0]) #left for now change later
        pic = pic.data 
    except IndexError:
        pass
    return pic, pic_type

def read_mp3(file_path:str):
    pic = None
    pic_type = None
    pic = mp3.MP3(file_path).tags # Can swap to mutagen.id3.ID3(file)? Not sure seems same but perhaps not though tags is of type mutagen.id3.ID3
    if pic:
        for opt in pic.keys():
            if opt.startswith("APIC") or opt.startswith("PIC"):
                pic = pic.get(opt)
                pic_type = "."+pic.mime[pic.mime.find("/")+1:] # this seems more reliable than mimetypes.guess_extension(pic.mime), as "image/jpg" not detected as .jpg for some reason
                pic = pic.data
                break
            
    return pic, pic_type

def read_image_from_music(tags:tag_utils.tags):
    if tags.file_type == "FLAC":
        pic, pic_type = read_flac(tags)
    elif tags.file_type == "MP3":
        # as must use MP3 and not EasyMP3 must reopen
        # not a big issue as most of my files are flac
        # TODO: Use ID3 / mp3.MP3 instead of EasyID3 / mp3.EasyMP3
        pic, pic_type = read_mp3(tags.file_path) 
        

    return pic, pic_type

def is_in_filetypes(string:str, types:list):
    if string[string.rfind(".")+1:] in types:
        return True
    
    return False

def image_search(root, dirs, files, recursive_depth=0):
    cover = None
    status = -1 # -1 None, 0 Any Image, 1 Front
    for file in files:
        if not is_in_filetypes(file, ["jpg", "jpeg", "png"]):
            continue
        if file[:file.rfind(".")].lower().endswith("cover"):
            return f"{root}\\{file}"
        if file[:file.rfind(".")].lower().endswith("front") and status < 1:
                cover = file
                status = 0
        if status < 0:
            cover = file
            status = 0

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