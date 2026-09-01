import os, json, shutil, subprocess
import ytmusicapi,spotify_scraper

PATH = open("path.txt","r").read()
LIBRARY = os.path.join(PATH,"Library")
PLAYLISTS = os.path.join(PATH,"Playlists")
os.makedirs(LIBRARY,exist_ok=True)
os.makedirs(PLAYLISTS,exist_ok=True)
os.makedirs("stuff",exist_ok=True)
pathsafe = lambda x: x.strip().replace(":",";").replace('<','[').replace('>',']').replace(':','"').replace('"',"'").replace("/","-").replace("\\","-").replace("|","-").replace("?","!").replace("*","+")[:150]
searchfmt = lambda t: f"{t.name} - {', '.join([i.name for i in t.artists])}"
getfn = lambda t: os.path.join(LIBRARY,f"{pathsafe(searchfmt(t))} {t.id}.mp3")

client = spotify_scraper.SpotifyClient()
fetchplaylists, fetchalbums, fetchtracks = [],[],[]
library, playlists = [],[]

for i in input('> ').split():
    if '/playlist/' in i: fetchplaylists.append(i)
    elif '/album/' in i: fetchalbums.append(i)
    elif "/track/" in i: fetchtracks.append(i)

class Track:
    def __init__(self,x,album=None):
        self.name = x.name
        self.id = x.id
        self.album = album or x.album
        self.artists = x.artists
        self.images = x.images if not album else album.images
        self.duration_ms = x.duration_ms
        self.track_number = x.track_number

for playlist in client.get_playlists(fetchplaylists, max_tracks=999):
    tracks = [Track(t.track) for t in playlist.unwrap().tracks]
    library += tracks
    fn=pathsafe(f"{playlist.result.name} {playlist.result.id}.m3u")
    file = open(fn,"w")
    file.write(f"#EXTM3U\n#PLAYLIST:{playlist.result.name}")
    for t in tracks:
        file.write(f"#EXTINF:{t.duration_ms//1000},{searchfmt(t)}\n{getfn(t)}")
    file.close()
    shutil.copy(fn,os.path.join(PLAYLISTS,fn))
    os.remove(fn)

for album in client.get_albums(fetchalbums):
    library += [Track(i,album.result) for i in album.unwrap().tracks]
library += [Track(i.unwrap()) for i in client.get_tracks(fetchtracks)]

threads = []
ytm = ytmusicapi.YTMusic()

for track in library:
    fn = getfn(track)
    if not os.path.exists(fn):
        print(searchfmt(track))
        if f"{track.album.id}.jpg"not in os.listdir("stuff"):
            client.download_cover(track,"stuff",size="largest",filename=f"{track.album.id}.jpg")
        for found in ytm.search(searchfmt(track))[:10]:
            try:
                if found['resultType']in['song','video']:
                    subprocess.run(["yt-dlp","-t","mp3","-o",os.path.join("stuff",track.id),
                        found['videoId']],capture_output=True)
                    subprocess.run(["ffmpeg","-i",os.path.join("stuff",f"{track.id}.mp3"),"-i",os.path.join("stuff",f"{track.album.id}.jpg"),
                        "-map","0:a","-map","1:v","-c","copy",
                        "-id3v2_version","3",
                        "-metadata:s:v",'comment="Cover (front)',
                        "-metadata","title="+track.name,
                        "-metadata","artist="+track.artists[0].name,
                        "-metadata","album="+track.album.name,
                        "-metadata","album_artist="+track.album.id,
                        "-metadata","track="+str(track.track_number),
                        f"{track.id}.mp3"],capture_output=True)
                    shutil.copy(f"{track.id}.mp3",fn)
                    break
            except Exception as e: print(track.name,e)
        else: print(f"{track.name} fail")

for i in os.listdir("stuff"):
    os.remove(os.path.join('stuff',i))
client.close()
