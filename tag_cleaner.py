# Fix window Shit
import os
from mutagen import flac

# TODO: Depreciate this shit

def clean(tags):
    # Clean tags
    # Found issues in some songs of these tags being highly duplicated
    for tag in ["GENRE", "COMPOSER", "ARTIST", "ARTISTS"]:
        try:
            temp = tags[tag]
        except KeyError:
            continue

        unique = list()
        for i in temp:
            if i in unique:
                continue
            unique.append(i)

        tags[tag] = unique
    return tags

def traverse(path, overwrite=False):
    # Read Directories
    print(f"----- Current Path: {path}")
    directories = os.popen(f"dir /B /AD {path}").read().rstrip()
    if (directories == "File Not Found"):
        directories = list()
    else:
        directories = directories.split("\n")

    for directory in directories:
        if (directory != "" and not directory.endswith(" CONVERT")):
            traverse(f'{path[:-1]}\\{directory}"', overwrite)

    # Read songs
    songs = os.popen(f"dir /B /A-D-S-H {path}").read().rstrip()
    if (songs == "File Not Found"):
        songs = list()
    else:
        songs = songs.split("\n")

    # Clean for flac/mp3
    new_songs = list()
    for song in songs:
        if song.endswith(".mp3") or song.endswith(".flac"):
            new_songs.append(song)
    print(f"--- Songs: {new_songs}\n")
    # Gate no songs
    if (len(new_songs) <= 0):
        return

    # Clean songs
    for song in new_songs:
        file = f'{path[:-1]}\\{song}'[1:]
        print(f"\n-- {song} --")
        print(f"- Read: {file}")

        # Load and clean Tags
        if file.endswith(".flac"):
            flac_file = flac.Open(file)
            tags = clean(flac_file.tags)
            flac_file.tags = tags
            flac_file.save()
        
## ONLY WORKS FOR FLAC

if __name__ == "__main__":
    music_dir = "D:\\Music"#sys.argv[1]
    overwrite = False
    traverse(f'"{music_dir}"', overwrite)
    
        
    
