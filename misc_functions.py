# this uses the python open() function plus my own code so i can cache reads - LucasVL
# there is really very little reason for this to exist, it kinda simplifies my code maybe but all of this would be similarly fast if i just gave in and used a database. that being said, i have never had good experiences with databases, and greatly prefer using the filesystem for its simplicity. thats why i made this, to get the speed benefits of a DB with the simplicity and flexibility of files scattered around in folders.
# on an NVMe drive, the speed boost is very minimal, however on hard drives this would provide a noticable increase in speed as this primarily optimises for random reads to many small files

class read_cached:
    """Syntax: read_cached(filename) returns requested file contents, caching them so next time this is called it has it all saved. read_cached.clear_entry(file) will take a file and remove it from the cache, effectively "refreshing" that file, as the next time it is needed it will be loaded back into cache"""
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

    def clear_entry(file):
        import os
        file = os.path.abspath(file)
        try:
            read_cached.cached.pop(file)
        except KeyError:
            return "File not found, ignored."

def get_post_content(postname, returnformat="html"):
    """Syntax: get_post_content(postname, "html (default), markdown/md, plaintext"), Gets a posts content from the cache and returns it in the requested format"""
    
    import re
    if not re.compile("^[0-9\-]*$").match(postname): # Makes sure the post name contains nothing it shouldnt
        from flask import abort
        abort(418)
        return 1 # if abort for some reason fails at least thisll catch it

    returnformat = returnformat.lower()
    page_content = read_cached(f"blogs/{postname}/page.md")
    
    if returnformat == "html":
        from markdown import markdown
        return markdown(page_content, extensions=['extra', 'codehilite', 'toc'])

    elif returnformat in ["markdown", "md"]:
        return page_content

    elif returnformat == "plaintext":
        # very much a hack, i frankly have no clue how python markdown cant just export text
        from markdown import markdown
        from bs4 import BeutifulSoup
        return BeautifulSoup(markdown(page_content), features='html.parser').get_text() # post (md) --> HTML --> beautifulsoup object --> text


def get_post_info(postname):
    """Does what it says on the tin. in goes post name, out comes a dict with all the info about the posts"""
    import re
    if not re.compile("^[0-9\-]*$").match(postname): # Makes sure the post name contains nothing it shouldnt
        from flask import abort
        abort(418)
        return 1 # if abort for some reason fails at least thisll catch it
    import json
    return json.loads(read_cached(f"blogs/{postname}/db.json"))


def limit_content_length(max_length):
    """shamelessly copy/pasted from https://stackoverflow.com/questions/25036498/is-it-possible-to-limit-flask-post-data-size-on-a-per-route-basis - allows me to limit the max POST size on a per route basis. super useful for when im processing multiple data types and want to set different limits for say, a logged in user vs a non logged in user"""
    from functools import wraps
    from flask import request, abort
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            cl = request.content_length
            if cl is not None and cl > max_length:
                abort(413)
            return f(*args, **kwargs)
        return wrapper
    return decorator
