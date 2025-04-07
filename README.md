# Music Matcher (FMCSPD.py)
A command line tool to export Spotify playlists alongside local audio files.

FMCSPD - Folder Music Converter and Spotify Playlists Downloader.

# Comandline Options
<pre>
 LOGGING
 -v / --verbose : Enable Verbose Mode
 -l / --log : Enable Logging
 --log-file <file> : file log should save to
                     DEFAULT: log.txt

 CONVERTING
 --bitrate <bitrate> : desired export bitrate
                       DEFAULT: 192k
 -o / --overwrite-music : Overwrite already converted music, without will only overwrite files with size == 0 in bytes
 -b / --use-blacklist : ignore directiores in blacklist.txt
 --image-depth <depth> : Maximum folder depth to look for a cover file
                         -1 = infinite recursion,
                          0 = No below folders, 
                         >0 = That number of folders lower than file 
                         DEFAULT: -1
 --threads <# of threads>: desired number of threads to convert songs with, roughly correlates to # of ffmpeg processes
                         DEFAULT: min(32, os.cpu_count() + 4)
 --retag-only : don't convert new songs, only re-tag existing converted songs.

 SPOTIFY
 --redirect-uri <url> : URL to redirect handler. use {PORT} for port and it will be replaced by the set port
                        DEFAULT: "http://localhost:{PORT}/callback"
 --port <port> : Redirect port
                 DEFAULT: 3000
 --authorise-retries <times to retry> : Sets the number of times to retry spotify authorisation
                                        DEFAULT: 1
 --client-id <id> : Will override client id set in "client_id.txt"
 --secret <secret> : Will override secret set in "secret.txt"
 -c / --cache : Cache the formated, not filtered, responses from spotify
 --cache-status <value> : Status of caches desired to be used
                         -1 = Don't use any caches,
                          0 = Use only the cached playlists but get new tracks in playlists
                          1 = Use the cached tracks, doesn't need to get data from spotify # As of now will still authenticate
                         DEFAULT: -1

 PLAYLIST FILTER
 --min-playlist-songs <number> : Minimum number of songs in a playlist to create/match it
                                 DEFAULT: 1
 --owned-by-user <spotify username / -1> : As of now only one user whos playlists to create.match
                                           -1 = Only requesting user
                                           DEFAULT: Will use any user
 -m / --collaborative : Create/match collaborative playlists
 
 MATCHER
 -t / --use-cached-converted : Use cached converted tracks
 -c / --cache : Cache the formated tracks in converted folder
 -p / --omit-song-album-postfixes : Omit anything after (inclusive), " - ", "(", "[" in song names or album names
                                    used when local files track names differ from spotify, eg, "Romantic Flight [3m25]" and "Romantic Flight - From How To Train Your Dragon Music From The Motion Picture"
                                    DEFAULT: requries a mostly exact match, ie, some stripping and case insensitivity
 --playlist-path-location <path> : Use when the converted music will be stored elsewhere
                                   DEFAULT: will use converted path (arg[0])
 --output-path <path> : Path to where output folders will be created and filled with matched playlists
                        DEFAULT: Current working directory

 arg[0] : Directory with music to convert
</pre>

# Example Arguments
## Overwrite output Music for android
```Bash
py FMCSPD.py -v -l --bitrate 128k -o -b -c --min-playlist-songs 5 --owned-by-user -1 -p --playlist-path-location "\storage\emulated\0\Music\Music_CONVERTED" "D:\Music"
```

## No caches Android
```Bash
py FMCSPD.py -v -l --bitrate 128k -b -c --min-playlist-songs 5 --owned-by-user -1 -p --playlist-path-location "\storage\emulated\0\Music\Music_CONVERTED" "D:\Music"
```

## Local and Spotify unchanged (use all caches)
```Bash
py FMCSPD.py -v -l --bitrate 128k -b --cache-status 1 --min-playlist-songs 5 -p --owned-by-user -1 -t -p --playlist-path-location "\storage\emulated\0\Music\Music_CONVERTED" "D:\Music"
```

## Spotify unchanged (use Spotify caches, re-cache converted)
```Bash
py FMCSPD.py -v -l --bitrate 128k -b -c --cache-status 1 --min-playlist-songs 5 -p --owned-by-user -1 -p --playlist-path-location "\storage\emulated\0\Music\Music_CONVERTED" "D:\Music"
```
