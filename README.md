# FMCSPD
Folder Music Compressor and Spotify Playlists Download

Fresh for android
py FMCSPD.py -v -l --bitrate 96k -o -b -c --min-playlist-songs 5 --owned-by-user -1 --playlist-path-location "\storage\emulated\0\Music\Music_CONVERTED" "D:\Music"

No Caches Android
py FMCSPD.py -v -l --bitrate 96k -b -c --min-playlist-songs 5 --owned-by-user -1 --playlist-path-location "\storage\emulated\0\Music\Music_CONVERTED" "D:\Music"

Local and spotify unchanged (use all caches)
py FMCSPD.py -v -l --bitrate 96k -b -c --cache-status 1 --min-playlist-songs 5 --owned-by-user -1 -t --playlist-path-location "\storage\emulated\0\Music\Music_CONVERTED" "D:\Music"

spotify unchanged (use spotify caches, re-cache converted)
py FMCSPD.py -v -l --bitrate 96k -b -c --cache-status 1 --min-playlist-songs 5 --owned-by-user -1 --playlist-path-location "\storage\emulated\0\Music\Music_CONVERTED" "D:\Music"