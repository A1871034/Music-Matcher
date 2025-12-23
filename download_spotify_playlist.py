import requests
import json
import time
import webbrowser
import random
import string
import socket
import json
from datetime import datetime
from base64 import b64encode

from logger import logger

class spotify():
    def __init__(self, CLIENT_SECRET, CLIENT_ID, REDIRECT_URI = "http://127.0.0.1:{PORT}/callback", PORT=3000, MAX_AUTHORISE_RETRIES=1, log = None):
        self.CLIENT_SECRET = CLIENT_SECRET
        self.CLIENT_ID = CLIENT_ID
        self.PORT = PORT
        self.REDIRECT_URI = REDIRECT_URI.format(PORT = PORT)
        self.MAX_AUTHORISE_RETRIES = MAX_AUTHORISE_RETRIES
        self.log = log
        if not self.log:
            self.log = logger("spotify_log.txt", True, False)

        self.log_settings()

        self.authorise()

    def log_settings(self):
        self.log.log("\n---- Spotify Settings")
        self.log.log(f"        CLIENT_SECRET: {self.CLIENT_SECRET}")
        self.log.log(f"            CLIENT_ID: {self.CLIENT_ID}")
        self.log.log(f"                 PORT: {self.PORT}")
        self.log.log(f"         REDIRECT_URI: {self.REDIRECT_URI}")
        self.log.log(f"MAX_AUTHORISE_RETRIES: {self.MAX_AUTHORISE_RETRIES}")

    def send_http_close(self):
        pass

    def authorise(self):
        now = time.time()
        self.log.log("\n---- Starting Authorisation ----")
        try:
            with open("cache/tokens.json", "r") as f:
                data = json.loads(f.read())
                if data["expires"] > now:
                    self.log.log("-- Using cached token")
                    self.access_token = data["access_token"]
                    self.access_token_type = data["token_type"]
                    return
                self.log.log("-- Cached token expired")
        except (FileNotFoundError, json.decoder.JSONDecodeError):
            self.log.log("-- Invalid or No \"tokens.json\"")

        self.log.log("-- Getting new authorisation code")
        scope = "playlist-read-private user-library-read"
        state = "".join(random.choices(string.ascii_letters+string.digits,k=16))
        self.log.log("Opening browser login page")
        webbrowser.open(f"https://accounts.spotify.com/authorize?client_id={self.CLIENT_ID}&response_type=code&redirect_uri={self.REDIRECT_URI}&state={state}&scope={scope}",new=1)

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("localhost", self.PORT))
            s.listen(1)
            conn, addr = s.accept()
            with conn:
                self.log.log(f"Connection recieved on {addr}")
                while True:
                    data = conn.recv(1024)
                    if data.startswith(b"GET /callback?"):
                        self.log.log("Callback Recieved")
                        with open("auto_close.html", "rb") as f:
                            response_body = f.read()
                        response_headers = {
                            'Content-Type': 'text/html; encoding=utf8',
                            'Content-Length': len(response_body),
                            'Connection': 'close',
                        }
                        response_headers_raw = ''.join(f"{key}: {value}" for key, value in response_headers.items())
                        conn.send(b"HTTP/1.1 200 OK")
                        conn.send(response_headers_raw.encode("utf-8"))
                        conn.send(b"\n")
                        conn.send(response_body)
                        conn.close()
                        self.log.log("Sent HTML and closed connection")
                        break
                    if not data: break
        # below is obviously shit but don't feel like learning how to do it properly rn
        data = data.decode().split(" ")[1].split("&")
        code = data[0][data[0].find("=")+1:]
        recv_state = data[1][data[1].find("=")+1:]
        
        if recv_state != state:
            self.log.log(f"Recieved State, \"{recv_state}\", != Sent State \"{state}\"")
            raise Exception("State returned from spotify != sent state")

        self.log.log("-- Requesting access_token")

        data = requests.post("https://accounts.spotify.com/api/token",
                      headers={
                          "Content-Type": "application/x-www-form-urlencoded",
                          "Authorization": "Basic " + b64encode(f"{self.CLIENT_ID}:{self.CLIENT_SECRET}".encode()).decode()
                      },
                      data = f"grant_type=authorization_code&code={code}&redirect_uri={self.REDIRECT_URI}")
        if data.status_code != 200:
            self.log.log(f"-- Returned status code, {data.status_code}, != 200")
            raise requests.exceptions.HTTPError("Invalid Status Code "+data.status_code)
        data = data.json()
        data["expires"] = now+data["expires_in"]
        self.access_token = data["access_token"]
        self.access_token_type = data["token_type"]

        self.log.log("-- access_token recieved")

        with open("cache/tokens.json", "w") as f:
            f.write(json.dumps(data))

        self.log.log("-- access_token cached")

    def spotify_get(self, url, depth=0):
        self.log.log(f"GETTING: \"{url}\"")
        response = requests.get(url, headers={"Authorization": f"{self.access_token_type} {self.access_token}"})
        if response.status_code != 200:
            if response.status_code == 401 and depth < self.MAX_AUTHORISE_RETRIES:
                self.authorise()
                return self.spotify_get(url, depth+1)
            elif response.status_code == 429:
                self.log.log("RATE LIMIT HEADERS BELOW\n\n")
                self.log.log(response.headers)
                self.log.log("\n\nEND RATE LIMIT HEADERS")
                # TODO: IMPLEMENT "Retry-After" header field contains recomended seconds to wait
                #self.log.log("Rate limited, sleeping for: {}")
                #time.sleep()
                #return self.spotify_get(url, depth)
            else:
                self.log.log(f"FAILED - Get request with status {response.status_code}, \"{url}\"")
                return None
        self.log.log(f"SUCCESS")
        return response.json() 
    
class filterer():
    # TODO: Change OWNED_BY_USER to be from endpoint: https://api.spotify.com/v1/me
    def __init__(self, MIN_SONGS=None, OWNED_BY_USER=None, INCLUDE_COLLABORATIVE=None, log = None):
        self.MIN_SONGS = MIN_SONGS
        self.OWNED_BY_USER = OWNED_BY_USER
        self.INCLUDE_COLLABORATIVE = INCLUDE_COLLABORATIVE

        self.log = log
        if not self.log:
            self.log = logger("filterer_log.txt", True, False)
        

        self.log_settings()

    def log_settings(self):
        self.log.log("\n---- Filterer Settings")
        self.log.log(f"            MIN_SONGS: {self.MIN_SONGS}")
        self.log.log(f"        OWNED_BY_USER: {self.OWNED_BY_USER}")
        self.log.log(f"INCLUDE_COLLABORATIVE: {self.INCLUDE_COLLABORATIVE}")
    
    def filter_playlists(self, data, requesting_user):
        if self.OWNED_BY_USER == "-1":
            OWNED_BY_USER = requesting_user 
        else:
            OWNED_BY_USER = f"spotify:user:{self.OWNED_BY_USER}"

        self.log.log(f"\n-- Filtering {len(data)} Playlists")

        cum_minus = 0
        for i in range(len(data)):
            cur_data = data[i-cum_minus]
            remove = False
            if cur_data["img_url"]:
                collaborative = "blend-playlist-covers" in cur_data["img_url"] or cur_data["collaborative"]
            else:
                collaborative = cur_data["collaborative"]
            if cur_data["tracks_total"] < self.MIN_SONGS:
                remove = True
            elif (OWNED_BY_USER is not None) and cur_data["owner_uri"] != OWNED_BY_USER and not collaborative:
                remove = True
            elif collaborative and not self.INCLUDE_COLLABORATIVE:
                remove = True

            if remove:
                remove = False
                data.pop(i-cum_minus)
                cum_minus += 1

        
        self.log.log(f"{cum_minus} Playlists Removed")
        
        return data
    
class formater():
    def format_playlist_data(data):
        if data["total"] <= 0:
            return None
        
        formated = []
        for i in data["items"]:
            temp_obj = {"href":i["href"],
                        "name":i["name"].replace("\\", " ").replace("/"," "),
                        "owner_uri":i["owner"]["uri"],
                        "collaborative":i["collaborative"],
                        "tracks_href":i["tracks"]["href"],
                        "tracks_total":i["tracks"]["total"]}
            try:
                if (i["images"] is not None) and (len(i["images"]) > 0):
                    temp_obj["img_url"] = i["images"][0]["url"]
                else:
                    temp_obj["img_url"] = None
            except KeyError:
                pass
            formated.append(temp_obj)
        return formated

    def format_tracks(data):
        new = []
        for i in data:
            artists = []
            for artist in i["track"]["artists"]:
                artists.append(artist["name"])
            new.append({"name":i["track"]["name"],
                        "album":i["track"]["album"]["name"],
                        "artists":artists,
                        "duration_ms":i["track"]["duration_ms"],
                        "tracknumber":i["track"]["track_number"],
                        "added_at":i["added_at"],
                        "added_at_epoch":datetime.strptime(i["added_at"], "%Y-%m-%dT%H:%M:%SZ").timestamp()
                        })
        return new
    
class spotify_data():
    def __init__(self, spotify_object, filt, log=None):
        self.spotify = spotify_object
        self.filter = filt
        self.playlists = []
        self.tracks = []
        self.requesting_user = None
        self.log = log
        if not self.log:
            self.log = logger("spotify_data_log.txt",True,False)

    def chech_cache(self, file):
        try:
            with open(file, "r") as f:
                return json.loads(f.read())
        except (FileNotFoundError, json.decoder.JSONDecodeError):
            return -1

    def get_caches(self, cache_status):
        if cache_status == -1:
            return cache_status
        
        self.log.log(f"\n-- Checking Caches with status: {cache_status}")
        
        if cache_status == 1:
            data = self.chech_cache("cache/sp_tracks.json")
            if data == -1:
                self.log.log("cache/sp_tracks.json invalid or non-existent")
                cache_status = 0
            else:
                self.log.log("cache/sp_tracks.json loaded")
                self.tracks = data
        
        if cache_status == 0:
            data = self.chech_cache("cache/playlists.json")
            if data == -1:
                self.log.log("cache/playlists.json invalid or non-existent")
                cache_status = -1
            else:
                self.log.log("cache/playlists.json loaded")
                self.requesting_user = data["requesting_user"]
                self.playlists = data["data"]

        self.log.log(f"- resulting cache status: {cache_status}")

        return cache_status
    
    # cache_status, -1 use no caches, 0 use cached playlists, 1 use cached tracks
    def get_tracks(self, cache_status=-1, CACHE_RESULTS = True):
        cache_status = self.get_caches(cache_status)

        if cache_status == 1:
            return self.tracks

        if cache_status == -1:
            self.playlists = self.__get_playlists(CACHE_RESULTS=CACHE_RESULTS)

        self.tracks = self.__get_tracks(CACHE_RESULTS=CACHE_RESULTS)

        return self.tracks
    
    def __get_playlists(self, CACHE_RESULTS=True):
        self.log.log("\n-- Getting Playlists")
        nxt = "https://api.spotify.com/v1/me/playlists?limit=50"
        results = []
        num_found = 0
        while nxt:
            playlists = self.spotify.spotify_get(nxt)
            num_found += playlists["total"]
            results.extend(formater.format_playlist_data(playlists))
            nxt = playlists["next"]

            if not self.requesting_user:
                split_href = playlists["href"].split("/")
                self.requesting_user = f"spotify:user:{split_href[split_href.index('users')+1]}"            

        self.log.log(f"Got {len(results)} Playlists")

        if CACHE_RESULTS:
            self.log.log(f"Caching Playlists")
            with open("cache/playlists.json", "w") as f:
                f.write(json.dumps({"requesting_user":self.requesting_user, "data":results}, indent=2))
        
        return results
            
    def __get_tracks(self, CACHE_RESULTS=True):
        
        filtered_playlists = self.filter.filter_playlists(self.playlists, self.requesting_user)
        

        self.log.log("\n-- Getting Tracks")
        # Adds liked songs
        filtered_playlists.append({"name": "Liked Songs",
                                   'tracks_href': "https://api.spotify.com/v1/me/tracks"})

        tracks = {}
        for playlist in filtered_playlists:
            self.log.log(f"\n- Requesting Tracks from Playlist: \"{playlist['name']}\"")
            response = self.spotify.spotify_get(f"{playlist['tracks_href']}?limit=50&fields=next,items(added_at,track(name,album(name,genres),artists(name,genres),duration_ms,track_number))")
            if response is None:
                continue
            cur_tracks = []
            cur_tracks.extend(response["items"])
            while response["next"]:
                response = self.spotify.spotify_get(f"{response['next']}&fields=next,items(added_at,track(name,album(name,genres),artists(name,genres),duration_ms,track_number))")
                if response is None:
                    continue
                cur_tracks.extend(response["items"])

            cur_tracks = formater.format_tracks(cur_tracks) # will fail with same names but who has that and ill use id later
            cur_tracks.sort(key = lambda track: track["added_at_epoch"], reverse=True) 

            tracks[playlist["name"]] = cur_tracks
        

        if CACHE_RESULTS:
            self.log.log(f"\n- Caching Tracks")
            with open("cache/sp_tracks.json", "w") as f:
                f.write(json.dumps(tracks, indent=2))

        return tracks
        
        
if __name__ == "__main__":
    CLIENT_ID = "d9a4208678c44578ae9f5103c1a07d39"
    with open("secret.txt", "r") as f:
        SECRET = f.read().rstrip()

    CACHE_RESULTS=True
    cache_status=-1
    
    sp = spotify(SECRET, CLIENT_ID)
    filt = filterer(3, None, True)

    sp_data = spotify_data(sp, filt)
    sp_data.get_tracks(cache_status, CACHE_RESULTS)
