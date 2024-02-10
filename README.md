# Music Matcher

Overwrite Output Music for android
py FMCSPD.py -v -l --bitrate 128k -o -b -c --min-playlist-songs 5 --owned-by-user -1 -p --playlist-path-location "\storage\emulated\0\Music\Music_CONVERTED" "D:\Music"

No Caches Android
py FMCSPD.py -v -l --bitrate 128k -b -c --min-playlist-songs 5 --owned-by-user -1 -p --playlist-path-location "\storage\emulated\0\Music\Music_CONVERTED" "D:\Music"

Local and spotify unchanged (use all caches)
py FMCSPD.py -v -l --bitrate 128k -b --cache-status 1 --min-playlist-songs 5 -p --owned-by-user -1 -t -p --playlist-path-location "\storage\emulated\0\Music\Music_CONVERTED" "D:\Music"

spotify unchanged (use spotify caches, re-cache converted)
py FMCSPD.py -v -l --bitrate 128k -b -c --cache-status 1 --min-playlist-songs 5 -p --owned-by-user -1 --playlist-path-location "\storage\emulated\0\Music\Music_CONVERTED" "D:\Music"

