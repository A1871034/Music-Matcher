
# TODO: Actually make this shit useful and then used
class tags():
    def __init__(self, check_duplicates=True):
        # TODO: Could change later to make it do all tags but rn these are the only problematic ones
        if check_duplicates:
            self.duplicate_tags = ["GENRE", "COMPOSER", "ARTIST", "ARTISTS"]
        else:
            self.duplicate_tags = list()
        
    def clean(self, tags):
        for tag in self.duplicate_tags:
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
    
    # TODO: Tag Merger, especially for genres