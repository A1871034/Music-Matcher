class str_utils:
    def clean_tag_data(inp):
        # Probably will be used later to remove special chars
        # Cant remember why ' was removed previously
        out = inp
        if type(inp) == list:
            new_list = []
            for i in inp:
                if type(i) != str:
                    continue
                new_list.append(str_utils.__stripper(i)) #
            out = new_list
        elif type(inp) == str:
            out = str_utils.__stripper(inp) #
        
        if out is None and inp is not None:
            print("FUCKER")
            quit()

        return out
    
    def ensure_path_end_slash(path:str):
        if path.endswith("\\"):
            return path
        return path+"\\"
    
    def __stripper(s: str): # Fix this shit
        return s.strip().lower().replace("'", "").replace("\u2019", "").replace(",", "").replace("&","+")
