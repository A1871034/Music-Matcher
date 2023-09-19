class str_utils:
    def clean_tag_data(inp):
        # Probably will be used later to remove special chars
        # Cant remember why ' was removed previously
        out = inp
        if type(inp) == list:
            new_list = list()
            for i in inp:
                if type(i) != str:
                    continue
                new_list.append(i.strip().lower()) #.replace("'", "")
            out = new_list
        elif type(inp) == str:
            out = inp.strip().lower() #.replace("'", "")
        
        if out==None and inp!=None:
            print("FUCKER")
            quit()

        return out
    
    def ensure_path_end_slash(path:str):
        if path.endswith("\\"):
            return path
        return path+"\\"
