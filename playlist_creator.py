import json
import os
from pydub.utils import mediainfo
from pydub import AudioSegment
from logger import logger

class playlist:
    def __init__(self, name, OUTPUT_DIR, ):
        self.name=name
        self.data = ""
        self.song_count = 0
        self.OUTPUT_DIR = OUTPUT_DIR

    def write(self):
        if not os.path.isdir(self.OUTPUT_DIR):
            os.mkdir(self.OUTPUT_DIR)
        with open(f"{self.OUTPUT_DIR}{self.name}.m3u8", "w", encoding="utf-8", newline="\n") as f:
            f.write("#EXTM3U")
            f.write(self.data)

    def add_song(self, duration, song_name, artists, file_path):
        self.song_count += 1
        self.data+=(f"\n#EXTINF:{duration},{', '.join(artists)} - {song_name}\n")
        self.data+=(file_path)

# TODO: Reduce Scope
class song_matcher:
    def __init__(self, CONVERTED_ROOT_PATH, TRANSFERED_ROOT_PATH, OUTPUT_DIR, MIN_PLAYLIST_SONGS=3, USE_CACHED_TRACKS = False, CACHE=True, OMMIT_ALBUMS_SONG_POSTFIXES=False, log=None):
        self.CONVERTED_ROOT_PATH = self.ensure_path_end_slash(CONVERTED_ROOT_PATH)
        self.TRANSFERED_ROOT_PATH = self.ensure_path_end_slash(TRANSFERED_ROOT_PATH)
        self.OUTPUT_DIR = self.ensure_path_end_slash(OUTPUT_DIR)
        self.MIN_PLAYLIST_SONGS = MIN_PLAYLIST_SONGS
        self.USE_CACHED_TRACKS = USE_CACHED_TRACKS
        self.CACHE = CACHE
        self.OMMIT_ALBUMS_SONG_POSTFIXES = OMMIT_ALBUMS_SONG_POSTFIXES

        self.likely_false_negative = 0

        self.log = log
        if not self.log:
            self.log = logger("playlist_creator_log.txt", True, False)

        self.log_settings()

        self.tag_aliases = { # ordered by precedence descending
                "artists": ["artists", "artist", "artist_name", "album_artist"],
                "name": ["name", "title", "track_name"],
                "duration_ms": ["duration_ms", "durationms"], # So far have never matched this so sorta pointless
                "album": ["album", "album_name"],
                "track_number": ["track_number", "track"]
            }
        for key, val in self.tag_aliases.items(): # add UPPERCASE
            with_upper = list()
            for i in val:
                with_upper.append(i)
                with_upper.append(i.upper())
            self.tag_aliases[key] = with_upper

        self.formats = ["mp3", "flac"]
        
    
    class song_scorer:                
            def __init__(self, spotify_song, log):
                self.likely_false_negative = 0
                self.best_matches = {
                    "artists":0,
                    "name":0,
                    "duration_ms":0,
                    "album":0,
                    "track_number":0
                }
                self.best_song = None
                self.spotify_song = self.clean_spotify_song(spotify_song)
                self.log = log
                

            @staticmethod
            def clean_spotify_song(spotify_song):
                spotify_song["artists"] = song_matcher.string_cleaner(spotify_song["artists"])
                spotify_song["name"] = song_matcher.string_cleaner(spotify_song["name"])
                spotify_song["album"] = song_matcher.string_cleaner(spotify_song["album"])
                return spotify_song

            def matching_artists(self, song):
                s = 0
                for artist in self.spotify_song["artists"]: #TODO: Fix up  this shit like idk cmp func and reduce iteratively with reducing functions
                    matched = False
                    if artist in song["artists"]:
                        s += 1
                        continue

                    keyboard_artist = self.remove_non_keyboard_chars(artist)
                    for spot_artist in song["artists"]:
                        if keyboard_artist  == self.remove_non_keyboard_chars(spot_artist):
                            s += len(keyboard_artist)/len(artist)
                            matched = True
                            break
                    if matched:
                        continue

                    for spliter in [" / ", " & "]: # iffy and if / and & in name possibility of double match
                        for split_artist in artist.split(spliter):
                            if split_artist in song["artists"]:
                                self.log.log(f"Split Artist Matched: local \"{song['artists']}\", spotify \"{self.spotify_song['artists']}\" ")
                                s += len(split_artist)/len(artist)
                return s
            
            def duration_closeness(self, song):
                seconds_plus_minus = 10
                flatness = 0.5
                s_to_ms = 1000
                # No reason this cant be linear but have funny function now
                distance = abs(int(song["duration_ms"])-int(self.spotify_song["duration_ms"]))
                closeness = 1-(distance/(seconds_plus_minus*s_to_ms))**flatness
                return max(closeness,0)

            # Omits anything after a, " - ", "(", or "["
            @staticmethod
            def name_postfix_omitter(orig_name):
                name = orig_name.split(" ")
                word_starting_omitters = ["-", "(", "["]
                for i in range(1,len(name)): # Don't ommit start eg, "(What's The Story) Morning Glory?"
                    try:
                        if name[i][0] in word_starting_omitters:
                            return " ".join(name[:i])
                    except IndexError:
                        pass
                return orig_name
            
            @staticmethod
            def remove_non_keyboard_chars(str_in):
                keyboard_chars = "`1234567890-=qwertyuiop[]\\asdfghjkl;'zxcvbnm,./~!@#$%^&*()_+QWERTYUIOP{}|ASDFGHJKL:\"ZXCVBNM<>? "
                str_out = ""
                for char in str_in:
                    if char in keyboard_chars:
                        str_out += char
                return str_out 

            # Gets increasingly aggressive
            @staticmethod
            def prop_matches_a(str_a, str_b):
                clean_a = song_matcher.string_cleaner(str_a) # should already be clean
                clean_b = song_matcher.string_cleaner(str_b)
                if clean_a == clean_b:
                    return 1
                
                """keyboard_a = song_matcher.song_scorer.remove_non_keyboard_chars(str_a)
                keyboard_b = song_matcher.song_scorer.remove_non_keyboard_chars(str_b)
                if keyboard_a == keyboard_b:
                    return len(keyboard_a)/len(clean_a)"""
                
                postfix_ommited_a = song_matcher.song_scorer.name_postfix_omitter(clean_a)
                postfix_ommited_b = song_matcher.song_scorer.name_postfix_omitter(clean_b)

                if postfix_ommited_a == postfix_ommited_b:
                    return len(postfix_ommited_a)/len(clean_a)

                return 0

            def check_song(self, song):
                # Set base
                matched = {
                    "artists":0,
                    "name":0,
                    "duration_ms":0,
                    "album":0,
                    "track_number":0
                }

                self.cur_song = song

                matched["artists"] = self.matching_artists(song)
                matched["duration_ms"] = self.duration_closeness(song)
                matched["name"] = self.prop_matches_a(self.spotify_song["name"], song["name"])
                matched["album"] = self.prop_matches_a(self.spotify_song["album"], song["album"])
                matched["track_number"] = int(self.spotify_song["track_number"] == song["track_number"])

                return matched
            
            def cmp_songs(self, songs):
                for song in songs:
                    self.cmp_song(song)
                return self.best_song
            
            def not_mininmum_matched(self, match):
                if match["artists"] == 0:
                    if match["name"] != 0 and match["duration_ms"] != 0 and match["album"] != 0:
                        self.log.log(f"Likely False Positive: Song (\"{self.spotify_song['name']}\") but No Spotify Artist \"{self.spotify_song['artists']}\" in {self.cur_song['artists']}")
                        self.likely_false_negative += 1
                    return True

                if match["name"] == 0:
                    return True
                
                return False
            
            def cmp_song(self, song):
                song_matches = self.check_song(song)

                """if song["name"] == "tea for the tillerman" and self.spotify_song["name"] == "tea for the tillerman":
                    print(song_matches)
                    self.log.log(f"SONG: {song}")
                    self.log.log(f"SPOT: {self.spotify_song}")
                    quit()"""

                if self.not_mininmum_matched(song_matches):
                    #self.log.log(f"NOT MIN: {song['name']} | {self.spotify_song['name']}")
                    return

                for field, match_value in song_matches.items():
                    if match_value > self.best_matches[field]:
                        self.best_matches = song_matches
                        self.best_song = song
                        return
                    elif match_value < self.best_matches[field]:
                        return

    @staticmethod
    def ensure_path_end_slash(path):
        if path.endswith("\\"):
            return path
        return path+"\\"
    
    @staticmethod
    def string_cleaner(inp):
        # Probably will be used later to remove special chars
        # Cant remember why ' was removed previously
        out = inp
        if type(inp) == list:
            new_list = list()
            for i in inp:
                new_list.append(i.strip().lower()) #.replace("'", "")
            out = new_list
        elif type(inp) == str:
            out = inp.strip().lower() #.replace("'", "")
        
        if out==None and inp!=None:
            print("FUCKER")
            quit()

        return out

    @staticmethod
    def get_song_duration(mi, file_path):
        return len(AudioSegment.from_file(file_path))
    
    def log_settings(self):
        self.log.log("\n---- Song Matcher Settings")
        self.log.log(f"CONVERTED_ROOT_PATH: {self.CONVERTED_ROOT_PATH}")
        self.log.log(f"TRANSFERED_ROOT_PATH: {self.TRANSFERED_ROOT_PATH}")
        self.log.log(f"OUTPUT_DIR: {self.OUTPUT_DIR}")
        self.log.log(f"MIN_PLAYLIST_SONGS: {self.MIN_PLAYLIST_SONGS}")
        self.log.log(f"USE_CACHED_TRACKS: {self.USE_CACHED_TRACKS}")
        self.log.log(f"CACHE: {self.CACHE}")

    def read_song_data(self, file_path):
        self.log.log(file_path)
        mi = mediainfo(file_path)
        tags = mi.get('TAG',None)
        data = {
            "file_path": file_path
        }
        for tag in self.tag_aliases.keys():
            written = False
            if tag == "artists":
                for check_tag in self.tag_aliases[tag]:
                    try:
                        data[tag] = self.string_cleaner(tags[check_tag])
                        if type(data[tag]) == str:
                            data[tag] = data[tag].split(";") # Absolutely goofy but CBA to implement split at any rn
                            if len(data[tag]) == 1:
                                data[tag] = data[tag][0].split(",")
                            data[tag] = self.string_cleaner(data[tag])
                        written = True
                        break
                    except KeyError:
                        pass
                if not written:
                    data[tag] = list()
                continue
            
            for check_tag in self.tag_aliases[tag]:
                try:
                    data[tag] = self.string_cleaner(tags[check_tag])
                    written = True
                    break
                except KeyError:
                    pass
            if not written:
                if tag == "name":
                    self.log.log(f"FUCKER: {file_path}")
                data[tag] = None
                
        if data["duration_ms"] == None:
            data["duration_ms"] = self.get_song_duration(file_path)
            
        return data

    def is_song(self, file_path):
        for f in self.formats:
            if file_path.endswith("." + f):
                return True

        return False

    @staticmethod
    def concat_root(root, name):
        return root + "\\" + name

    def get_all_converted(self):
        self.log.log("-- Getting Song Library")
        self.songs = list()
        for root, dirs, files in os.walk(self.CONVERTED_ROOT_PATH):
            for file in files:
                if self.is_song(file):
                    self.songs.append(root+"\\"+file)

    def get_song_data(self):
        self.log.log("-- Getting Songs' Data")
        for i in range(len(self.songs)):
            self.songs[i] = self.read_song_data(self.songs[i])

    def match(self, song_spotify):
        #print(song_spotify["name"])
        scorer = self.song_scorer(song_spotify, self.log)
        best_match = scorer.cmp_songs(self.songs)
        self.likely_false_negative += scorer.likely_false_negative
        return best_match

    def cache_converted_songs(self):
        self.log.log("-- Caching Converted Tracks")
        with open("cache/all_converted_tracks.json", "w") as f:
            f.write(json.dumps(self.songs, indent=2))

    def song_method(self):
        self.get_all_converted()
        self.get_song_data()
        if self.CACHE:
            self.cache_converted_songs()
        
    def run(self, tracks):
        if self.USE_CACHED_TRACKS: # TODO: Seems to not be working
            try:
                with open("cache/all_converted_tracks.json", "r") as f:
                    self.songs = json.loads(f.read())
                self.log.log("-- Using cached converted tracks")
            except (FileNotFoundError, json.decoder.JSONDecodeError):
                self.log.log("-- Cached Converted Tracks file invalid or non-existent")
                self.song_method()
        else:
            self.song_method()

        num_matched = 0
        playlists_saved = 0
        
        for playlist_name, spotify_songs in tracks.items():
            self.log.log(f"\n-- Finding Matches for playlist: \"{playlist_name}\"")
            found = False
            num_matched_playlist = 0
            if None in spotify_songs:
                self.log.log("WHAT")
                self.log.log(str(spotify_songs))
            for song in spotify_songs:
                result = self.match(song)
                if result:
                    num_matched += 1
                    num_matched_playlist += 1
                    
                    if not found:
                        new_playlist_local = playlist(playlist_name, self.OUTPUT_DIR+"playlists_local\\")
                        if self.CONVERTED_ROOT_PATH != self.TRANSFERED_ROOT_PATH:
                            new_playlist_remote = playlist(playlist_name, self.OUTPUT_DIR+"playlists_remote\\")
                        found=True                   
                    new_playlist_local.add_song(result["duration_ms"], result["name"], result["artists"], result["file_path"])
                    if self.CONVERTED_ROOT_PATH != self.TRANSFERED_ROOT_PATH: # bad as its constant but who really cares definetly not the main time consumer
                        new_playlist_remote.add_song(result["duration_ms"], result["name"], result["artists"], result["file_path"].replace(self.CONVERTED_ROOT_PATH, self.TRANSFERED_ROOT_PATH))
            self.log.log(f"{num_matched_playlist} out of {len(spotify_songs)} Songs Matched")
            if num_matched_playlist >= self.MIN_PLAYLIST_SONGS:
                self.log.log(f"Writing playlist to \"{new_playlist_local.OUTPUT_DIR}{new_playlist_local.name}.m3u8\" ")
                new_playlist_local.write()
                if self.CONVERTED_ROOT_PATH != self.TRANSFERED_ROOT_PATH:
                    self.log.log(f"Writing playlist to \"{new_playlist_local.OUTPUT_DIR}{new_playlist_local.name}.m3u8\" ")
                    new_playlist_remote.write()
                playlists_saved += 1
            else:
                self.log.log(f"NOT SAVED: {num_matched_playlist} Matched < threshold {self.MIN_PLAYLIST_SONGS}")

        self.log.log("\n---- SUMMARY")
        self.log.log(f"Playlists Checked: {len(tracks)}")
        self.log.log(f"Playlists Saved: {playlists_saved}")
        self.log.log(f"Individual Song Matches: {num_matched} (Same songs in multiple playlists will count multiple times)")
        self.log.log(f"Likely False Negatives: {self.likely_false_negative} (Same songs in multiple playlists will count multiple times)")
if __name__ == "__main__":
    CONVERTED_ROOT_PATH = r"D:\Music_CONVERTED"
    TRANSFERED_ROOT_PATH = r"\storage\emulated\0\Music\Music_CONVERTED"
    OUTPUT_DIR = r"C:\Users\Xander\Documents\Coding\Flac to Mp3"
    USE_CACHED_TRACKS = False
    matcher = song_matcher(CONVERTED_ROOT_PATH, TRANSFERED_ROOT_PATH, OUTPUT_DIR, USE_CACHED_TRACKS=USE_CACHED_TRACKS)
    with open("cache/tracks.json", "r") as f:
        tracks = json.loads(f.read())
    matcher.run(tracks)

    

    
