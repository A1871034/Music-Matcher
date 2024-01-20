from json import dumps as json_dumps

class future_content:
    pass

class logger():
    def __init__(self, log_file, logging=True, mute=False, write_chunk_size=100000):
        # Asynchronous Logging
        self.unmerged_chars = 0
        self.submissions_in_progress = 0
        self.future_indexes = {}
        self.stream_locked = False
        self.future_id = 1

        self.submit_calls = 0
        self.get_calls = 0

        # General Logging 
        self.logging = logging
        self.mute = mute
        self.stream = ""
        self.write_chunk_len = write_chunk_size/2 # In Bytes/2 as utf 16 min is 2 bytes per char

        if self.logging:
            self.log_file = open(log_file, "w", encoding="u16")

    def log(self, out):
        if self.logging:
            if type(self.stream) is str:
                self.stream += out+"\n"
            else:
                self.stream.append(out+"\n")
        if not self.mute:
            print(out)

        self.check_len_write_stream()

    def check_len_write_stream(self):
        # Check async baloney
        if self.unmerged_chars >= self.write_chunk_len:
            self.merge_stream()

        if type(self.stream) is str:
            if len(self.stream) >= self.write_chunk_len:
                self.write_stream()
        elif type(self.stream) is list:
            if len(self.stream[0]) >= self.write_chunk_len:
                self.write_stream()

    # Future methods are not intended to be used for large amounts of coexisting futures
    def get_future(self) -> int: # To be called Syncronously
        self.get_calls += 1
        future_id = self.future_id
        self.future_id += 1
        
        if type(self.stream) is str:
            self.stream = [self.stream, future_id]
        else: # Must be list
            self.stream.append(future_id)

        return future_id

    def submit_future(self, future: int, output: str) -> None:
        self.submit_calls += 1
        # Lockout During a Merge
        while self.stream_locked:
            pass # busy waiting i know but shouldnt be too long

        self.submissions_in_progress += 1

        if future in self.future_indexes:
            self.stream[self.future_indexes[future]] = output
            del self.future_indexes[future]
        else:
            # Find future, add founds to future_indexes for others use
            # Should only get here after invalidating indexes
            for i in range(len(self.stream)):
                if self.stream[i] == future:
                    self.stream[i] = output
                elif type(self.stream[i]) is int:
                    self.future_indexes[future] = i

        self.unmerged_chars += len(output)

        self.submissions_in_progress -= 1

        if not self.mute:
            print(output)

    # Will be called synchronously
    def merge_stream(self):
        if type(self.stream) is str:
            return
        
        # Lock stream so no future can be submitted during a merge to avoid indexes changing
        self.stream_locked = True

        # Wait for any current submissions to finish
        while self.submissions_in_progress > 0:
            pass # busy waiting i know but shouldnt be too long

        # Invalidate stored future indexes
        # Its just easier than actually computing new ones
        self.future_indexes.clear()

        # Likely not most efficient but is simple and easy
        # Merge strs left
        i = len(self.stream) - 1
        while i >= 1:
            if type(self.stream[i-1]) is str and type(self.stream[i]) is str:
                # Reduce unmerged chars
                self.unmerged_chars += len(self.stream[i-1])

                # Merge down
                self.stream[i-1] = self.stream[i-1]+self.stream.pop(i)
                
                # Reduce unmerged chars
                self.unmerged_chars -= len(self.stream[i-1])
            i -= 1

        # No futures, reduce to str
        if len(self.stream) == 1:
            self.stream = self.stream[0]

        # Unlock stream
        self.stream_locked = False
        
    # TODO: FIX BUG, prepended newlines at very begining
    def write_stream(self, force = False):
        # Write as much as is initially merged if list otherwise write str
        if type(self.stream) is str:
            self.log_file.write(self.stream)
            self.stream = ""
        elif force:
            self.log_file.write(json_dumps(self.stream))
            self.stream = ""
        else:
            self.log_file.write(self.stream[0])
            self.stream[0] = "" # This line right here likely causing aforemention BUG

    def close(self):
        self.write_stream(force=True)
        self.log_file.close()
