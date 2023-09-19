import sys
import getopt
import traceback
from os import getcwd

from convert import converter
from logger import logger
from download_spotify_playlist import spotify, spotify_data, filterer
from playlist_creator import song_matcher

# LOGGING
# -v / --verbose : Enable Verbose Mode
# -l / --log : Enable Logging
# --log-file <file> : file log should save to
#                     DEFAULT: log.txt
#
# CONVERTING
# --bitrate <bitrate> : desired export bitrate
#                       DEFAULT: 192k
# -o / --overwrite-music : Overwrite already converted music, without will only overwrite files with size == 0 in bytes
# -b / --use-blacklist : ignore directiores in blacklist.txt
# --image-depth <depth> : Maximum folder depth to look for a cover file
#                         -1 = infinite recursion,
#                          0 = No below folders, 
#                         >0 = That number of folders lower than file 
#                         DEFAULT: -1
#
# SPOTIFY
# --redirect-uri <url> : URL to redirect handler. use {PORT} for port and it will be replaced by the set port
#                        DEFAULT: "http://localhost:{PORT}/callback"
# --port <port> : Redirect port
#                 DEFAULT: 3000
# --authorise-retries <times to retry> : Sets the number of times to retry spotify authorisation
#                                        DEFAULT: 1
# --client-id <id> : Will override client id set in "client_id.txt"
# --secret <secret> : Will override secret set in "secret.txt"
# -c / --cache : Cache the formated, not filtered, responses from spotify
# --cache-status <value> : Status of caches desired to be used
#                         -1 = Don't use any caches,
#                          0 = Use only the cached playlists but get new tracks in playlists
#                          1 = Use the cached tracks, doesn't need to get data from spotify # As of now will still authenticate
#                         DEFAULT: -1
#
# PLAYLIST FILTER
# --min-playlist-songs <number> : Minimum number of songs in a playlist to create/match it
#                                 DEFAULT: 1
# --owned-by-user <spotify username / -1> : As of now only one user whos playlists to create.match
#                                           -1 = Only requesting user
#                                           DEFAULT: Will use any user
# -m / --collaborative : Create/match collaborative playlists
# 
# MATCHER
# -t / --use-cached-converted : Use cached converted tracks
# -c / --cache : Cache the formated tracks in converted folder
# -p / --omit-song-album-postfixes : Omit anything after (inclusive), " - ", "(", "[" in song names or album names
#                                    used when local files track names differ from spotify, eg, "Romantic Flight [3m25]" and "Romantic Flight - From How To Train Your Dragon Music From The Motion Picture"
#                                    DEFAULT: requries a mostly exact match, ie, some stripping and case insensitivity
# --playlist-path-location <path> : Use when the converted music will be stored elsewhere
#                                   DEFAULT: will use converted path (arg[0])
# --output-path <path> : Path to where output folders will be created and filled with matched playlists
#                        DEFAULT: Current working directory
#
# arg[0] : Directory with music to convert

class parser():
    def __init__(self, argv):
        try:
            self.options, self.args = getopt.getopt(argv, "vlobcmtcp",
                               ["verbose",
                                "log",
                                "log-file=",
                                "bitrate=",
                                "overwrite-music",
                                "use-blacklist",
                                "image-depth=",
                                "redirect-uri=",
                                "port=",
                                "authorise-retries=",
                                "client-id=",
                                "secret=",
                                "cache",
                                "cache-status=",
                                "min-playlist-songs=",
                                "owned-by-user=",
                                "collaborative",
                                "use-cached-converted",
                                "omit-song-album-postfixes",
                                "playlist-path-location=",
                                "output-path="
                                ])
        except Exception as err:
            print(err)
            sys.exit()

        self.set_defaults()
        self.set_opts()

    @staticmethod
    def remove_path_quotations(path):
        if path.startswith("\""):
            path = path[1:]
        if path.endswith("\""):
            path = path[:-1]
        return path

    def set_opts(self):
        for o, a in self.options:
            # LOGGING
            if o in ("-v", "--verbose"):
                self.MUTE = False 
            elif o in ("-l", "--log"):
                self.LOGGING = True
            elif o == "--log-file":
                self.LOG_FILE = self.remove_path_quotations(a)

            # CONVERTING
            elif o == "--bitrate":
                self.BITRATE = a
            elif o in ("-b", "--use-blacklist"):
                self.USE_BLACKLIST = True
            elif o in ("-o", "--overwrite-music"):
                self.OVERWRITE = True
            elif o == "--image-depth":
                self.IMAGE_DEPTH = int(a)

            # SPOTIFY
            elif o == "--redirect-uri":
                self.REDIRECT_URI = a
            elif o == "--port":
                self.PORT == int(a)
            elif o == "--authorise-retries":
                self.MAX_AUTHORISE_RETRIES = int(a)
            elif o == "--client-id":
                self.CLIENT_ID = a
            elif o == "--secret":
                self.SECRET = a
            elif o in ("-c", "--cache"):
                self.CACHE_RESULTS = True
            elif o == "--cache-status":
                self.cache_status = int(a)
            
            # PLAYLIST FILTER
            elif o == "--min-playlist-songs":
                self.MIN_SONGS_IN_PLAYLIST = int(a)
            elif o == "--owned-by-user":
                self.OWNED_BY_USER = a
            elif o in ("-m", "--collaborative"):
                self.INCLUDE_COLLABORATIVE = True

            # MATCHER
            elif o in ("-t", "--use-cached-converted"):
                self.USE_CACHED_TRACKS = True
            elif o in ("-p", "--omit-song-album-postfixes"):
                self.OMMIT_ALBUMS_SONG_POSTFIXES = True
            elif o == "--playlist-path-location":
                self.TRANSFERED_ROOT_PATH = self.remove_path_quotations(a)
            elif o == "--output-path":
                self.OUTPUT_DIR = self.remove_path_quotations(a)
            else:
                assert False, f"Unhandled Option: {o}"

    def set_defaults(self):
        # LOGGING
        self.LOGGING = False
        self.MUTE = True
        self.LOG_FILE = "log.txt"

        # CONVERTING
        self.MUSIC_DIR = self.args[0]
        self.USE_BLACKLIST = False
        self.BITRATE = "192k"
        self.OVERWRITE = False
        self.IMAGE_DEPTH = -1

        # SPOTIFY DATA
        self.REDIRECT_URI = "http://localhost:{PORT}/callback"
        self.PORT = 3000
        self.MAX_AUTHORISE_RETRIES=1
        try:
            with open("client_id.txt", "r") as f:
                self.CLIENT_ID = f.read().rstrip()
        except FileNotFoundError:
            pass
        try:
            with open("secret.txt", "r") as f:
                self.SECRET = f.read().rstrip()
        except FileNotFoundError:
            pass
        self.cache_status = -1
        self.CACHE_RESULTS = False

        # PLAYLIST FILTER
        self.MIN_SONGS_IN_PLAYLIST = 1
        self.OWNED_BY_USER = None
        self.INCLUDE_COLLABORATIVE = False

        # MATCHER
        self.CONVERTED_ROOT_PATH = self.MUSIC_DIR+"_CONVERTED"
        self.TRANSFERED_ROOT_PATH = self.CONVERTED_ROOT_PATH
        self.OUTPUT_DIR = getcwd()
        self.USE_CACHED_TRACKS = False
        self.OMMIT_ALBUMS_SONG_POSTFIXES = False


def FMCSPD():
    try:
        print("---------------------- SETTINGS STAGE")
        settings = parser(sys.argv[1:])
        
        # LOG
        log = logger(log_file=settings.LOG_FILE, 
                    logging=settings.LOGGING,
                    mute=settings.MUTE)
        
        # CONVERT
        log.log("\n\n---------------------- CONVERSION STAGE")
        c = converter(path=settings.MUSIC_DIR, 
                    write_path=settings.CONVERTED_ROOT_PATH,
                    blacklist=settings.USE_BLACKLIST,
                    bitrate=settings.BITRATE,
                    overwrite=settings.OVERWRITE,
                    image_depth=settings.IMAGE_DEPTH,
                    log=log)
        c.convert()

        # SPOTIFY
        log.log("\n\n---------------------- SPOTIFY STAGE")
        sp = spotify(CLIENT_SECRET=settings.SECRET,
                    CLIENT_ID=settings.CLIENT_ID,
                    REDIRECT_URI=settings.REDIRECT_URI,
                    PORT=settings.PORT,
                    MAX_AUTHORISE_RETRIES=settings.MAX_AUTHORISE_RETRIES,
                    log=log)
                    
        filt = filterer(MIN_SONGS=settings.MIN_SONGS_IN_PLAYLIST,
                        OWNED_BY_USER=settings.OWNED_BY_USER,
                        INCLUDE_COLLABORATIVE=settings.INCLUDE_COLLABORATIVE,
                        log=log)
        sp_data = spotify_data(spotify_object=sp, filt=filt, log=log)
        sp_data.get_tracks(cache_status=settings.cache_status,
                        CACHE_RESULTS=settings.CACHE_RESULTS)
        log.log("\n\n---------------------- MATCHING STAGE")
        # MATCH / CREATE PLAYLISTS
        matcher = song_matcher(CONVERTED_ROOT_PATH=settings.CONVERTED_ROOT_PATH,
                            TRANSFERED_ROOT_PATH=settings.TRANSFERED_ROOT_PATH,
                            OUTPUT_DIR=settings.OUTPUT_DIR,
                            MIN_PLAYLIST_SONGS=settings.MIN_SONGS_IN_PLAYLIST,
                            USE_CACHED_TRACKS=settings.USE_CACHED_TRACKS,
                            CACHE=settings.CACHE_RESULTS,
                            OMMIT_ALBUMS_SONG_POSTFIXES=settings.OMMIT_ALBUMS_SONG_POSTFIXES,
                            log=log)

        matcher.run(sp_tracks=sp_data.tracks, track_info=c.cached_converted)

        log.log("\n\n-------------- SUCCESS ---------- SUCCESS ---------- SUCCESS --------------")

        log.close()
    except (Exception, KeyboardInterrupt) as err:
        log.log("\n\n ------ ENDED WITH BELOW EXCEPTION ------")
        log.log(traceback.format_exc())
        log.close()

if __name__ == "__main__":
    FMCSPD()
    