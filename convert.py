from pydub import AudioSegment
import os
import time
import json

from logger import logger
import music_image_reader
import tag_utils

# TODO: Only use mutagen for media tags / info
class converter():
    def __init__(self, path, write_path="", blacklist=False, bitrate="192k", overwrite=False, image_depth=-1, log = None):
        self.path = path
        self.write_path = write_path
        self.use_blacklist = blacklist
        self.bitrate=bitrate
        self.overwrite=overwrite
        self.image_depth=image_depth
        self.log = log
        self.CACHED_CONVERTED_FILE_PATH = "cache/all_converted_tracks.json"
        if not self.log:
            self.log = logger("converter_log.txt", True, False)

        self.log.log(f"-- Initialised With Below:")
        self.log_settings()

        self.load_blacklist()

    def load_converted_cache(self):
        try:
            with open(self.CACHED_CONVERTED_FILE_PATH, "r") as f:
                self.cached_converted = json.load(f)
        except FileNotFoundError:
            self.cached_converted = {}

    def cache_converted(self):
        with open(self.CACHED_CONVERTED_FILE_PATH, "w") as f:
            f.write(json.dumps(self.cached_converted,indent=2))

    def log_settings(self):
        self.log.log(f"""- Settings:\nMusic Folder: {self.path}\nOutput Folder: {self.write_path}\nExporting Bitrate: {self.bitrate}\nOverwrite Songs with > 0 bytes: {self.overwrite}\nMax album folder depth to find cover images: {self.image_depth}\n""")

    def load_blacklist(self):
        if self.use_blacklist:
            with open("blacklist.txt", "r") as f:
                self.blacklist = f.read().strip().split("\n")
            self.log.log(f"Loaded blaclist of length {len(self.blacklist)} from blacklist.txt")
        else:
            self.blacklist = []

    def convert(self):
        self.start_time = time.time()
        self.log.log(f"Conversion Started at time {self.start_time}")

        self.create_converted_dir()

        self.load_converted_cache()

        try:
            self.walk_convert()
            self.cache_converted()
        except (Exception, KeyboardInterrupt) as err:
            self.cache_converted()
            raise err

        self.end_time = time.time()
        self.log.log(f"Conversion Ended at time {self.end_time}")

        duration = self.end_time - self.start_time
        self.log.log(f"Run Duration: {round(duration,1)}s OR {round(duration/60,0)}m")

        if len(self.failed) == 0:
            self.log.log("NONE FAILED")
        else:
            self.log.log(f"---- {len(self.failed)} SONGS FAILED: ↵")
            for i in self.failed:
                self.log.log(i)

    def walk_convert(self):
        # Walk Directories
        self.failed = list()
        self.log.log("--------------- WALKING & CONVERTING ---------------")
        for root, dirs, files in os.walk(self.path):
            self.log.log(f"\n---------------------\n----- Current Path: \"{root}\"")
            if root in self.blacklist:
                self.log.log("--- SKIPPING, Path in blacklist ---")
                dirs.clear()
                continue

            # Clean for flac/mp3
            # TODO: with more file types should be made more dynamic
            new_songs = list()
            for file in files:
                if file.endswith(".mp3") or file.endswith(".flac"):
                    new_songs.append(file)

            # Gate no songs 
            dir_created = False
            if (len(new_songs) <= 0):
                self.log.log("---- NO SONGS FOUND ----")
                continue
    
            self.log.log("---- Songs: ↵\n"+"\n".join(new_songs))

            # Find Image
            cover = music_image_reader.image_search(root, dirs, files, self.image_depth)

            # Create Converted Dir
            if not dir_created:
                folder_existed=False
                write_path = root.replace(self.path, self.write_path)
                try:
                    os.makedirs(write_path)
                except FileExistsError:
                    folder_existed=True

            # Convert Songs
            self.convert_songs(new_songs, root, write_path, cover, folder_existed)
        self.log.log("--------------- DONE WALKING & CONVERTING ---------------")

    def convert_songs(self, songs, root, write_path, cover=None, folder_existed=False):
        # Convert songs
        for song in songs:
            file = f'{root}\\{song}'
            new_file = f'{write_path}\\{song[:song.rfind(".")]}.mp3'

            self.log.log(f"\n--- {song}")

            # Gate already done songs
            if not self.overwrite and folder_existed:
                try:
                    if self.cached_converted[new_file]["modified_time"] == os.path.getmtime(file) and os.path.getsize(new_file) > 0:
                        self.log.log(f"- Existing File: ↵ (> 0b) & (Base File Unmodified)\n{new_file}\n-- SKIPPED") 
                        continue
                    else: # File exists but modified time !=
                        self.log.log(f"-- Existing File: Base File Modified or Converted File 0b (CONTINUING)\n{new_file}")
                except (OSError, KeyError):
                    pass               
        
            self.log.log(f"- Read: {file}")
            self.log.log(f"- Write: {new_file}")

            # Load File
            try:
                s = AudioSegment.from_file(file, format=song[song.rfind(".")+1:])
            except Exception as err:
                self.log.log(f"------- FAILED LOADING FILE -------\n{err}\n-----------------------")
                self.failed.append(file)
                continue

            # Load Tags
            tags_obj = tag_utils.tags(file)

            # TODO: merge directly below into tag_utils
            # Check For Embeded Image
            pic, pic_type = music_image_reader.read_image_from_music(tags_obj)
            if (pic and pic_type):
                cover = f"{root}\\temp_cover{pic_type}"
                self.log.log(f"- Embeded Cover Found -")
                with open(cover, "wb") as f:
                    f.write(pic)
            else:
                self.log.log(f"- Using Cover: {cover}")

            if tags_obj.tags:
                self.log.log("- Tags: ↵")
                for key, val in tags_obj.tags.items():
                    display_str = val.replace("\n", "\\n")
                    MAX_DISPLAY_LEN = 51
                    display_str = val if len(val) <= MAX_DISPLAY_LEN else val[:MAX_DISPLAY_LEN-3]+"...+"+str(len(val)-MAX_DISPLAY_LEN)
                    self.log.log(f"{key}: \"{display_str}\"") # Perhaps val will be an int one day :( wont worry about that now though
            else:
                self.log.log("-- NO TAGS FOUND")

            # Will overwrite but haven't found any with it and its updating with a correct value anyway. so don't care
            tags_obj.tags["duration_ms"] = len(s) # len(s) == duration in ms of s which is orig song
            
            # Try Exporting
            try:
                s.export(new_file, format="mp3", bitrate=self.bitrate,tags=tags_obj.tags, cover=cover)
                failed = False
            except Exception as err:
                self.log.log(f"------- FAILED EXPORTING FILE -------\n{err}\n-----------------------")
                self.failed.append(file)
                failed = True

            if not failed: # 
                tags_obj.clean_tags()
                tags_obj.add_filepath_tag()
                tags_obj.add_mdate_written()
                #tags_obj.ensure_has_durationms(s) # Should be redundant
                self.cached_converted[new_file] = tags_obj.tags

            if (pic and pic_type):
                os.system(f"del \"{cover}\"")
        
    def create_converted_dir(self):
        if not self.write_path:
            self.write_path = self.path+"_CONVERTED"

        try:
            os.mkdir(self.write_path)
            self.log.log(f"Created Exports Folder: \"{self.write_path}\"")
        except FileExistsError:
            self.log.log(f"Exports Folder Already Exists at: \"{self.write_path}\"")
            pass
    
# If there are errors Run Tag Cleaner First
# TODO: Not have to do above dumbass
if __name__ == "__main__":
    # Log Settings
    logging = True
    mute = False
    file = "convert_log.txt"
    
    log = logger(file, logging, mute)

    # Convert Settings
    music_dir = "D:\\Music"#sys.argv[1]
    bitrate = "96k"
    overwrite = False
    image_depth = -1 # -1 for infinite recursion, 0 for none 1+ for that number depth
    
    try:
        c = converter(music_dir, bitrate=bitrate, blacklist=True, overwrite=overwrite, image_depth=image_depth, log=log)
        c.convert()
    except KeyboardInterrupt as Err:
        log.log("------------ Keyboard Interrupt ------------")
    except Exception as Err:
        log.log("------------ UNCAUGHT EXCEPTION ------------")
        log.log(str(Err))

    # Close log File
    log.close()

    
        
    
