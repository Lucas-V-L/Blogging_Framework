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

# the 2 gradient functions are from https://www.cocyer.com/python-pillow-generate-gradient-image-with-numpy/
# i have 0 clue how they work, but they are absolutely amazing
def get_gradient_2d(start, stop, width, height, is_horizontal):
    import numpy as np
    if is_horizontal:
        return np.tile(np.linspace(start, stop, width), (height, 1))
    else:
        return np.tile(np.linspace(start, stop, height), (width, 1)).T
                    
def get_gradient_3d(width, height, start_list, stop_list, is_horizontal_list):
    import numpy as np
    result = np.zeros((height, width, len(start_list)), dtype=float)
    for i, (start, stop, is_horizontal) in enumerate(zip(start_list, stop_list, is_horizontal_list)):
        result[:, :, i] = get_gradient_2d(start, stop, width, height, is_horizontal)
    return result

def random_gradient(width, height):
    """Generates a random gradient at the specified resolution"""
    import numpy as np
    from PIL import Image
    import random
    array = get_gradient_3d(width, height,\
            (random.randint(0, 255),\
            random.randint(0, 255),\
            random.randint(0, 255)),\
            (random.randint(0, 255),\
            random.randint(0, 255),\
            random.randint(0, 255)),\
            (random.choice([True, False]),
                random.choice([True, False]),\
                random.choice([True, False])))
    return Image.fromarray(np.uint8(array))

def crop_scale_image(inputimg, width, height):
    """Basically crops and scales a supplied image and does what background size cover does in css"""
    from PIL import Image
    img = Image.open(inputimg)
    imgwidth, imgheight = img.size
    if imgwidth / imgheight < width / height:
        img = img.crop((0,\
            (imgheight-(imgwidth*(height/width)))/2,\
            imgwidth,\
            ((imgheight-(imgwidth*(height/width)))/2) + (imgwidth*(height/width))))
    elif imgwidth / imgheight > width / height:
        img = img.crop(((imgwidth-(imgheight*(width/height)))/2,\
                0,\
                ((imgwidth-(imgheight*(width/height)))/2) + (imgheight*(width/height)),\
                imgheight))
    img = img.resize((width, height))
    return img

def break_text(txt, font, max_width):
    """i would explain this but frankly i have no clue how it really works and im afraid to touch it. i spent 4 hours fixing just 1 tiny bug. if you need to edit this function for any reason you're better off just ditching the whole system that relies on it and giving up. this code is literal hell, god help me when all the deprecated shit i used gets removed"""
    txt = txt.split()
    subset = 1
    letter_size = None

    text_size = len(txt)
    while len(txt) > 0:
        debug = False
        
        while True:
            if debug:
                print(txt)
                import time
                time.sleep(1)
            txttmp = ""
            for index, i in enumerate(txt):
                txttmp += " " + i
                if debug: 
                    print(f'"{txttmp}"')
                    print(f"index: {index} subset: {subset}")
                if index >= subset: break
            if debug: print(f"index: {index} subset: {subset}")
            txttmp = txttmp.strip()
            width = font.getlength(txttmp)

            if width < max_width and len(txt) > 1 and len(txt) > subset:
                subset += 1
            elif width > max_width and subset != 1:
                subset -= 1
                txttmp = ""
                for index, i in enumerate(txt):
                    txttmp += " " + i
                    if index == subset: break
                txttmp = txttmp.strip()
                break
            elif width == max_width:
                break
            elif subset == 1 or subset == len(txt): 
                if not(width > max_width): break
                temp = ""
                for index, i in enumerate(txttmp):
                    if i == " ": break
                    temp += i
                    width = font.getlength(temp)
                    if width >= max_width:
                        txt = [txttmp[:index], txttmp[index:txttmp.find(" ")]] + txt[subset:]
                        break
                subset = 0
                txttmp = txt[0]
                break

        yield txttmp
        txt = txt[subset+1:]
        subset = 1

def random_word(length):
    import secrets, string
    letters = string.ascii_letters + string.digits
    return ''.join(secrets.choice(letters) for i in range(length))

def make_captcha(secret_key):
    """Returns HTML for a captcha. captcha.validate() validates a captcha"""
    from captcha.image import ImageCaptcha
    from captcha.audio import AudioCaptcha
    import base64, secrets, io, hashlib, json
    try:
        with open("captcha_db.json", "r") as captcha_db:
            used_captchas = json.loads(captcha.read())
    except:
        used_captchas = []
    
    while True:
        captcha_text = random_word(7).lower() # i would include uppercase chars, but that makes audio captchas much harder and i want this to be accessible
        salt = secrets.token_hex(15)
        captcha_hash = hashlib.sha256(f"{captcha_text}{salt}{secret_key}".encode("utf-8")).hexdigest() # the secret key is to prevent people from making their own combination of text and salt, this adds another factor which cannot be tampered with
        if captcha_hash not in used_captchas: break
    image = ImageCaptcha(fonts=["fonts/iosevka-extended-medium.ttf"])
    imagedata: io.BytesIO = image.generate(captcha_text)
    b64image = f'<img src="data:image/png;base64,{base64.b64encode(imagedata.read()).decode(encoding="utf-8")}" alt="Captcha Image"/>'
    audio = AudioCaptcha("captcha_voices/en")
    audiodata: bytearray = audio.generate(captcha_text)
    b64audio = f'<audio controls src="data:audio/wav;base64,{base64.b64encode(audiodata).decode(encoding="utf-8")}"></audio>'
    form = f'<input type="hidden" name="captcha_hash" value="{captcha_hash}">\
            <input type="hidden" name="captcha_salt" value="{salt}">\
            <label for="captcha_input">Captcha Text: </label><input type="text" name="captcha_input" id="captcha_input">'
    return f"{b64image}<br>{b64audio}<br>{form}<br>"
    
def check_captcha(secret_key, salt, text, captcha_hash_old):
    import hashlib, json
    try:
        with open("captcha_db.json", "r") as captcha_db:
            used_captchas = json.loads(captcha_db.read())
    except:
        used_captchas = []
    captcha_hash = hashlib.sha256(f"{text}{salt}{secret_key}".encode("utf-8")).hexdigest()
    if captcha_hash in used_captchas:
        return False
    elif captcha_hash == captcha_hash_old:
        used_captchas.append(captcha_hash)
        with open("captcha_db.json", "w") as captcha_db:
            captcha_db.write(json.dumps(used_captchas))
        return True
    else:
        return False
