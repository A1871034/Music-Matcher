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
            self.spotify_song = self.clean_spotify_song(spotify_song)
            self.log = log
            

        @staticmethod
        def clean_spotify_song(spotify_song):
            spotify_song["artists"] = str_utils.clean_tag_data(spotify_song["artists"])
            spotify_song["name"] = str_utils.clean_tag_data(spotify_song["name"])
            spotify_song["album"] = str_utils.clean_tag_data(spotify_song["album"])
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
            clean_a = str_utils.clean_tag_data(str_a) # should already be clean
            clean_b = str_utils.clean_tag_data(str_b)
            if clean_a == clean_b:
                return 1
            
            # Below was having no effect
            """keyboard_a = song_matcher.song_scorer.remove_non_keyboard_chars(str_a)
            keyboard_b = song_matcher.song_scorer.remove_non_keyboard_chars(str_b)
            if keyboard_a == keyboard_b:
                return len(keyboard_a)/len(clean_a)"""
            
            postfix_ommited_a = song_scorer.name_postfix_omitter(clean_a)
            postfix_ommited_b = song_scorer.name_postfix_omitter(clean_b)

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