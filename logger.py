class logger():
    def __init__(self, log_file, logging=True, mute=False, write_chunk_size=100000):
        self.logging = logging
        self.mute = mute
        self.stream = ""
        self.write_chunk_len = write_chunk_size/2 # In Bytes/2 as utf 16 min is 2 bytes per char

        if self.logging:
            self.log_file = open(log_file, "w", encoding="u16")

    def log(self, out):
        if self.logging:
            self.stream += out+"\n"
        if not self.mute:
            print(out)
        if len(self.stream) >= self.write_chunk_len:
            self.write_stream()

    def write_stream(self):
        self.log_file.write(self.stream)
        self.stream = ""

    def close(self):
        self.write_stream()
        self.log_file.close()
