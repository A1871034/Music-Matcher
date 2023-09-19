from mutagen import mp3, flac
from pydub import AudioSegment
from os.path import getmtime

from string_utils import str_utils

def get_song_duration(file_path):
    return len(AudioSegment.from_file(file_path))

class tags:
    tag_aliases = { # ordered by precedence descending
            "artists": ["artists", "artist", "artist_name", "album_artist"],
            "name": ["name", "title", "track_name"],
            "duration_ms": ["duration_ms", "durationms"], # So far have never matched this so sorta pointless
            "album": ["album", "album_name"],
            "tracknumber": ["track_number", "track", "tracknumber"]
        }
    for key, val in tag_aliases.items(): # add UPPERCASE
        with_upper = []
        for i in val:
            with_upper.append(i)
            with_upper.append(i.upper())
        tag_aliases[key] = with_upper
    
    def __init__(self, file_path):
        self.file_path = file_path
        self.get_file_tags(file_path)
        
    def get_file_tags(self, file_path):
        if file_path.endswith(".flac"):
            self.file_thing = flac.FLAC(file_path)
            data = dict(self.file_thing.tags)
            self.file_type = "FLAC"
        elif file_path.endswith(".mp3"):
            self.file_thing = mp3.EasyMP3(file_path)
            data = dict(self.file_thing.tags)
            self.file_type = "MP3"

        # collapse what should be non lists and put into form expected from before when using pydub.utils.mediainfo
        # TODO: remove things done to faciliate pydub
        for key in data.keys():
            if type(data[key]) == list and len(data[key]) == 1:
                new_val = data[key][0]
            elif type(data[key]) == list:
                new_val = ";".join(data[key]).strip()
            else:
                new_val = data[key]

            # As Flac tags are not meant to be null terminated
            # when they, are mutagen will output a string like, "<artist>\x00"
            if len(new_val) > 0 and new_val[-1] == "\x00":
                new_val = new_val[:-1]

            data[key] = new_val

        self.tags = data

    def clean_tags(self):
        data = {}
        for tag in self.tag_aliases.keys():
            written = False
            if tag == "artists":
                for check_tag in self.tag_aliases["artists"]:
                    try:
                        data["artists"] = str_utils.clean_tag_data(self.tags[check_tag])
                        if type(data["artists"]) == str:
                            data["artists"] = data["artists"].split(";") # Absolutely goofy but CBA to implement split at any rn
                            if len(data["artists"]) == 1:
                                data["artists"] = data["artists"][0].split(",")
                            data["artists"] = str_utils.clean_tag_data(data["artists"])
                        written = True
                        break
                    except KeyError:
                        pass
                if not written:
                    data["artists"] = []
                continue
            
            for check_tag in self.tag_aliases[tag]:
                try:
                    data[tag] = str_utils.clean_tag_data(self.tags[check_tag])
                    written = True
                    break
                except KeyError:
                    pass
            if not written:
                data[tag] = None
        self.tags = data
    
    def ensure_has_durationms(self, audio_segment:AudioSegment=None):
        if audio_segment is not None:
            self.tags["duration_ms"] = len(audio_segment)

        try:
            if self.tags["duration_ms"] is not None:
                return
        except KeyError:
            pass

        self.tags["duration_ms"] = get_song_duration(self.file_path)

    def add_filepath_tag(self):
        self.tags["file_path"] = self.file_path

    def add_mdate_written(self, file_path=None):
        if file_path is None:
            file_path = self.file_path
        
        self.tags["modified_time"] = getmtime(file_path)
