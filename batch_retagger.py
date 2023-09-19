import os
import mimetypes
import sys
import getopt
from mutagen import flac, mp3, easyid3

# TODO: Rewrite all of this

class retagger:
    def __init__(self, args):
        self.dist = {
            "list_tags":self.list_tags,
            "list_tag_fields":self.list_tag_fields,
            "batch_retag":self.batch_retag,
            "help":self.help
        }
        self.args = args
        self.opt = self.args[0]
        self.file = None

    def help(self):
        help_info = \
"""batch_retagger.py [opt] [dir/file] [*args]
opt: list_tags | list_tagfields | batch_retag
    list_tags = File: lists all tags, Dir: lists all unique values for tags of all files in dir
    list_tag_fields = File: list all tag fields, Dir: list all unique tag fields of all files in dir
    batch_retag [TAG] [new_value] = Modifies all files in dir, file[TAG] = new_value
help: print this
"""
        print(help_info)

    def init_path(self):
        self.path = self.args[1]
        self.reader = tag_reader(self.path)

    def run(self):
        self.dist[self.opt]()

    def list_tags(self):
        self.init_path()
        data = self.reader.get_tags()
        
        # Printing baloeny
        collated = {}
        for i in data:
            if type(i) == list:
                iterable = i
            elif type(i) == easyid3.EasyID3:
                iterable = i.items()
            else:
                raise Exception("not list or dict OOF")
            for key, val in iterable:
                if key in collated.keys() and val not in collated[key]:
                    collated[key].append(val)
                else:
                    collated[key] = [val]

        for key, val in collated.items():
            pp_val = "\""+str(val[0])
            for i in val[1:-1]:
                pp_val += "\", \""+ str(i)
            pp_val += "\""
            print(f"\t{key}: {pp_val}")

    def list_tag_fields(self):
        self.init_path()
        data = self.reader.get_tag_fields()

        # Printing baloney
        print(data) 

    def batch_retag(self):
        field = self.args[2]
        new_value = self.args[3]

        self.init_path()
        if not os.path.isdir(self.path):
            print("ONLY DIRS CAUSE IM LAZY AND ITS HARDER TO USE THIS")
            return
        
        data = self.reader.get_tags()
        
        # Printing baloeny
        collated = {}
        for i in data:
            if type(i) == list:
                iterable = i
            elif type(i) == easyid3.EasyID3:
                iterable = i.items()
            else:
                raise Exception("not list or dict OOF")
            for key, val in iterable:
                if key in collated.keys() and val not in collated[key]:
                    collated[key].append(val)
                else:
                    collated[key] = [val]

        try:
            if len(collated[field]) > 1:
                pp_val = "\""+str(val[0])
                for i in val[1:-1]:
                    pp_val += "\", \""+ str(i)
                pp_val += "\""

                inp = input(f"\"{field}\" has many values:\n{pp_val}\Set all to \"{new_value}\"? Y|N: ")
                if inp.lower() != "y":
                    return
        except KeyError:
            inp = input(f"Key Not Found: Would you like to add field \"{field}\" with value \"{new_value}\" to all files? Y|N: ")
            if inp.lower() != "y":
                return
            
        for file in os.listdir(self.path):
            if self.path.endswith("\\"):
                self.file = self.path+file
            else:
                self.file = self.path+"\\"+file
            self.retag_file(field, new_value)
            
            
    def retag_file(self, field, new_value):
        mime = mimetypes.guess_type(self.file)
        data = []
        if mime[0] == 'audio/x-flac':
            data = flac.FLAC(self.file)
            data[field] = new_value
        elif mime[0] == 'audio/mpeg':
            data = mp3.EasyMP3(self.file)
            data[field] = [new_value]
        else:
            #print(f"mime: {mime} | file: {self.file}")
            return
        
        
        data.save()


            
class tag_reader():
    def __init__(self, path):
        self.path = path

    def run_dir_run_file(self, run_if_dir, run_if_file):
        if os.path.isdir(self.path):
            return run_if_dir()
        elif os.path.isfile(self.path):
            self.file = self.path
            return run_if_file()

        raise FileNotFoundError

    def get_tags(self):
        return self.run_dir_run_file(self.get_dir_file_tags, self.get_file_tags)

    def get_tag_fields(self):
        return self.run_dir_run_file(self.get_dir_file_tag_fields, self.get_file_tag_fields)

    # Tag fields lisiting
    def get_file_tag_fields(self):
        data = self.get_file_data()
        return [i[0] for i in data]

    def get_dir_file_tag_fields(self):
        files = os.listdir(self.path)
        data = []
        for file in files:
            if self.path.endswith("\\"):
                self.file = self.path+file
            else:
                self.file = self.path+"\\"+file
            for i in self.get_file_tag_fields():
                if i not in data:
                    data.append(i)
        return data

    # Tag listing
    def get_file_tags(self):
        data = self.get_file_data()
        return data

    def get_dir_file_tags(self):
        files = os.listdir(self.path)
        data = []
        for file in files:
            if self.path.endswith("\\"):
                self.file = self.path+file
            else:
                self.file = self.path+"\\"+file
            data.append(self.get_file_tags())
        return data

    # Get Data
    def get_file_data(self):
        mime = mimetypes.guess_type(self.file)
        data = []
        if mime[0] == 'audio/x-flac':
            data = self.get_flac_data()
        elif mime[0] == 'audio/mpeg':
            data = self.get_mp3_data()
        else:
            #print(f"mime: {mime} | file: {self.file}")
            pass
        return data

    def get_flac_data(self):
        data = flac.FLAC(self.file)
        return data.tags

    def get_mp3_data(self):
        data = mp3.EasyMP3(self.file)
        return data.tags



if __name__ == "__main__":
    options, args = getopt.getopt(sys.argv[1:], "", [""])
    print(args)
    #args = ["batch_retag", r"D:\Music_CONVERTED\Catch 22\Keasbey Nights (1998) [CD-FLAC]", "albumartist", "Catch 22"]
    retag = retagger(args)
    retag.run()
