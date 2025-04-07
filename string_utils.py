class str_utils:
    @staticmethod
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
            out = str_utils.__stripper(inp)
        return out
    
    @staticmethod
    def ensure_path_end_slash(path:str):
        if path.endswith("\\"):
            return path
        return path+"\\"
    
    @staticmethod
    def __stripper(s: str):
        character_blacklist = ["'", "\u2019"]
        new_str = ""
        prev_c = None
        for c in s:
            if (c not in character_blacklist) and not ((prev_c == " ") and (c == " ")):
                new_str += c
                prev_c = c
        return new_str.strip().lower()
    
    @staticmethod
    def remove_non_keyboard_chars(str_in):
        keyboard_chars = "`1234567890-=qwertyuiop[]\\asdfghjkl;'zxcvbnm,./~!@#$%^&*()_+QWERTYUIOP{}|ASDFGHJKL:\"ZXCVBNM<>? "
        str_out = ""
        for char in str_in:
            if char in keyboard_chars:
                str_out += char
        return str_out
    
    # Omits anything after a, " - ", "(", or "["
    @staticmethod
    def name_postfix_omitter(orig_name):
        name = orig_name.split(" ")
        word_starting_omitters = ["-", "(", "["]
        for i in range(1,len(name)): # Don't ommit start eg, "(What's The Story) Morning Glory?"
            try:
                if name[i][0] in word_starting_omitters:
                    return " ".join(name[:i])
            except IndexError:
                pass
        return orig_name 
