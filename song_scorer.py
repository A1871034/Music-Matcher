from string_utils import str_utils

class song_scorer:                
    def __init__(self, spotify_song, log):
        self.likely_false_negative = 0
        self.best_matches = {
            "artists":0,
            "name":0,
            "duration_ms":0,
            "album":0,
            "tracknumber":0
        }
        self.best_song = None
        self.matched_splits = set()

        self.NAME_THRESHOLD = 0.5

        self.spotify_song = self.clean_spotify_song(spotify_song)
        self.log = log
        
    @staticmethod
    def clean_spotify_song(spotify_song):
        spotify_song["artists"] = str_utils.clean_tag_data(spotify_song["artists"])
        spotify_song["name"] = str_utils.clean_tag_data(spotify_song["name"])
        spotify_song["album"] = str_utils.clean_tag_data(spotify_song["album"])
        return spotify_song

    def matching_artists(self, song):
        splitters = [" / ", " & ", " feat. "]
        song_artists_split = set(song["artists"])
        for splitter in splitters:
            [song_artists_split.update(artists.split(splitter)) for artists in song["artists"]]
        
        s = 0
        for artist in self.spotify_song["artists"]: #TODO: Fix up  this shit like idk cmp func and reduce iteratively with reducing functions
            matched = False
            if artist in song["artists"]:
                s += 1
                continue

            keyboard_artist = str_utils.remove_non_keyboard_chars(artist)
            for spot_artist in song["artists"]:
                if keyboard_artist  == str_utils.remove_non_keyboard_chars(spot_artist):
                    s += len(keyboard_artist)/len(artist)
                    matched = True
                    break
            if matched:
                continue

            for spliter in splitters: # iffy and if / and & in name possibility of double match
                for split_artist in artist.split(spliter):
                    if split_artist in song_artists_split:
                        to_print = str(song_artists_split) + str(self.spotify_song['artists'])
                        if (to_print not in self.matched_splits):
                            self.log.log(f"Split Artist Matched: local \"{song_artists_split}\", spotify \"{self.spotify_song['artists']}\" ")
                            self.matched_splits.add(to_print)
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

    # Gets increasingly aggressive
    @staticmethod
    def prop_matches_a(str_a, str_b):
        if ((str_a is None) or (str_b is None)):
            return 0

        clean_a = str_utils.clean_tag_data(str_a) # should already be clean
        clean_b = str_utils.clean_tag_data(str_b)
        if clean_a == clean_b:
            return 1
        
        # Below was having no effect
        """keyboard_a = str_utils.remove_non_keyboard_chars(str_a)
        keyboard_b = str_utils.remove_non_keyboard_chars(str_b)
        if keyboard_a == keyboard_b:
            return len(keyboard_a)/len(clean_a)"""
        
        pfo_ratio = 0
        postfix_ommited_a = str_utils.name_postfix_omitter(clean_a)
        postfix_ommited_b = str_utils.name_postfix_omitter(clean_b)
        if postfix_ommited_a == postfix_ommited_b:
            pfo_ratio = len(postfix_ommited_a)/len(clean_a)
            pfo_ratio = max(pfo_ratio, len(postfix_ommited_b)/len(clean_b))
        
        # Strip string to only alphanumeric
        str_strip_ratio = 0
        str_strip_a = str_utils.only_alphanumeric(clean_a)
        str_strip_b = str_utils.only_alphanumeric(clean_b)
        if str_strip_a == str_strip_b:
            str_strip_ratio = len(str_strip_a)/len(clean_a)
            str_strip_ratio = max(str_strip_ratio, len(str_strip_b)/len(clean_b))

        return max(pfo_ratio, str_strip_ratio)

    def check_song(self, song):
        # Set base
        matched = {
            "artists":0,
            "name":0,
            "duration_ms":0,
            "album":0,
            "tracknumber":0
        }

        self.cur_song = song

        matched["artists"] = self.matching_artists(song)
        matched["duration_ms"] = self.duration_closeness(song)
        matched["name"] = self.prop_matches_a(self.spotify_song["name"], song["name"])
        matched["album"] = self.prop_matches_a(self.spotify_song["album"], song["album"])
        matched["tracknumber"] = int(self.spotify_song["tracknumber"] == song["tracknumber"])

        return matched
    
    def cmp_songs(self, songs):
        for song in songs.values():
            self.cmp_song(song)
        return self.best_song
    
    def not_mininmum_matched(self, match):
        if match["artists"] == 0:
            if match["name"] != 0 and match["duration_ms"] != 0 and match["album"] != 0:
                self.log.log(f"Likely False Negative: Song (\"{self.spotify_song['name']}\") but No Spotify Artist \"{self.spotify_song['artists']}\" in {self.cur_song['artists']}")
                self.likely_false_negative += 1
                return False
            return True

        if match["name"] < self.NAME_THRESHOLD:
            return True
        
        return False
    
    def cmp_song(self, song):
        song_matches = self.check_song(song)

        if self.not_mininmum_matched(song_matches):
            # self.log.log(f"NOT MIN: {song['name']} | {self.spotify_song['name']}")
            return

        for field, match_value in song_matches.items():
            if match_value > self.best_matches[field]:
                self.best_matches = song_matches
                self.best_song = song
                return
            
            if match_value < self.best_matches[field]:
                return
            