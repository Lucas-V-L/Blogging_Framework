# this uses the python open() function plus my own code so i can cache reads - LucasVL

class read_cached:
    try: cached
    except: cached = {}

    def __new__(self, file):
        import os
        self.file = os.path.abspath(file)
        
        try:
            return read_cached.cached[self.file]
        except: 
            with open(self.file, "r") as contents:
                read_cached.cached[self.file] = self.contents = contents.read()
            return self.contents
