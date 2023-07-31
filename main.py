#!/usr/bin/env python3

# use http://www.patorjk.com/software/taag to make labels

from flask import Flask, render_template, abort, send_from_directory, session, redirect, request, flash, make_response, url_for
from misc_functions import read_cached, get_post_content, get_post_info, limit_content_length, get_gradient_2d, get_gradient_3d
from PIL import Image
import numpy as np
import json, hashlib, os, time, shutil, base64, random

from config import *

# makes sure this always runs from the folder its in, otherwise it breaks
abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

app = Flask(__name__)


with open("db.json", "r") as dbfile:
    db = json.loads(dbfile.read())

with open("users.json", "r") as userdb:
    users = json.loads(userdb.read())

logged_in_db = {}
past_used_keys = []

@app.route("/", methods=["GET"])
def homepage():
    return render_template("index.html", \
            site_name = CONF_SITE_NAME,\
            categories = db["categories"],\
            featured = db["featured"],\
            allposts = os.listdir("blogs/"),\
            get_post_info = get_post_info)

#
#  /$$$$$$$   /$$$$$$   /$$$$$$  /$$$$$$$$       /$$    /$$ /$$$$$$ /$$$$$$$$ /$$      /$$ /$$$$$$$$ /$$$$$$$ 
# | $$__  $$ /$$__  $$ /$$__  $$|__  $$__/      | $$   | $$|_  $$_/| $$_____/| $$  /$ | $$| $$_____/| $$__  $$
# | $$  \ $$| $$  \ $$| $$  \__/   | $$         | $$   | $$  | $$  | $$      | $$ /$$$| $$| $$      | $$  \ $$
# | $$$$$$$/| $$  | $$|  $$$$$$    | $$         |  $$ / $$/  | $$  | $$$$$   | $$/$$ $$ $$| $$$$$   | $$$$$$$/
# | $$____/ | $$  | $$ \____  $$   | $$          \  $$ $$/   | $$  | $$__/   | $$$$_  $$$$| $$__/   | $$__  $$
# | $$      | $$  | $$ /$$  \ $$   | $$           \  $$$/    | $$  | $$      | $$$/ \  $$$| $$      | $$  \ $$
# | $$      |  $$$$$$/|  $$$$$$/   | $$            \  $/    /$$$$$$| $$$$$$$$| $$/   \  $$| $$$$$$$$| $$  | $$
# |__/       \______/  \______/    |__/             \_/    |______/|________/|__/     \__/|________/|__/  |__/
#
# REGULAR POST VIEWER
#
@app.route("/posts/<postname>", methods=["GET"])
def viewpost(postname):
    content = get_post_content(postname)
    info = get_post_info(postname)
 
    return render_template("page.html", content=content, title=info["title"], site_name=CONF_SITE_NAME)
#
# IMAGE HANDLER
#
@app.route("/posts/<postname>/images/<imgname>", methods=["GET"])
def serve_image(postname, imgname):
    return send_from_directory("blogs", f"{postname}/images/{imgname}")
#
# PLAINTEXT VIEWER
#
@app.route("/posts/<postname>/plaintext", methods=["GET"])
def viewpost_plaintext(postname):
    plaintext = get_post_content(postname)
    response = make_response(plaintext, 200) # turns the text into a response object so we can give it a mimetype
    response.mimetype = "text/plain"
    return response

#
#   /$$$$$$  /$$$$$$$  /$$      /$$ /$$$$$$ /$$   /$$
#  /$$__  $$| $$__  $$| $$$    /$$$|_  $$_/| $$$ | $$
# | $$  \ $$| $$  \ $$| $$$$  /$$$$  | $$  | $$$$| $$
# | $$$$$$$$| $$  | $$| $$ $$/$$ $$  | $$  | $$ $$ $$
# | $$__  $$| $$  | $$| $$  $$$| $$  | $$  | $$  $$$$
# | $$  | $$| $$  | $$| $$\  $ | $$  | $$  | $$\  $$$
# | $$  | $$| $$$$$$$/| $$ \/  | $$ /$$$$$$| $$ \  $$
# |__/  |__/|_______/ |__/     |__/|______/|__/  \__/
# 
# MAIN ADMIN PAGES - all on one app.route to have them all controlled by the same login system - this reduces boilerplate and makes it faster to patch any possible security related issues
#
@app.route("/admin/<page>/<argument>", methods=["GET", "POST"])
@app.route("/admin/<page>", methods=["GET", "POST"])
@app.route("/admin", methods=["GET", "POST"])
@limit_content_length(512 * 1024 * 1024) # 512mb size limit per request for uploads to the admin page
def admin(page=None, argument=None):
    # nothing should be before this if statement, this controls the login <-- ***IMPORTANT***
    # IF ANYTHING EVER RETURNS BEFORE THIS CHECK, IT WILL BYPASS LOGIN AND DESTROY ALL SECURITY!!!!!!!!!!!!!!!!!!!!!!!
    user_id = session.get("key")
    if not user_id in logged_in_db: # this redirects to the login page if the cookie does not exist or is tampered with
        return redirect("/admin/login", code=302)
    elif time.time() - logged_in_db[user_id]["last_access"] > CONF_STAY_LOGGED_IN_DURATION or \
            time.time() - logged_in_db[user_id]["initial_access"] > CONF_TOTAL_STAY_LOGGED_IN_DURATION:
        logged_in_db.pop(session.pop("key", None))
        return redirect("/admin/login", code=302) # signs user out and redirects to login if login is expired
    else: 
        logged_in_db[user_id]["last_access"] = time.time()
        username = logged_in_db[user_id]["uname"]
#
# KEEPALIVE - not a user facing page but for behind the scenes stuff
#
    if page == "login-keepalive" and CONF_ENABLE_LOGIN_KEEPALIVE: # adds time to initial access, but rate limited. this is so that a script on the editor page can keep the user from being logged out before they can save their work. also keeps the last access topped up because its a ping to the admin page
        if time.time() - logged_in_db[user_id]["last_keepalive"] > 110: 
            logged_in_db[user_id]["initial_access"] += 120 
            logged_in_db[user_id]["last_keepalive"] = time.time()
            return ('', 204)
        else: abort(429)
#
# DASHBOARD
#
    if page == None: # if no page is supplied, return the admin dashboard
        if request.method == "GET":
            return render_template("admin.html", username=username, posts=os.listdir("blogs/"), get_post_info=get_post_info)
        elif request.method == "POST": # if the method is post, the user has done something
            action = request.form["action"]
            if action == "delete":
                postname = request.form["postname"]
                if postname == db["featured"]:
                    return "Featured posts cannot be deleted, please feature a different post before deleting"
                if postname in os.listdir("blogs/"): # if its in the blogs dir, its safe because it already exists
                    shutil.rmtree(f"blogs/{postname}")
                    for category in db["categories"]: # remove the post from its category in the DB
                        try: db["categories"][category].pop(db["categories"][category].index(postname))
                        except ValueError: pass
                    for urgency in db["urgencies"]: # remove the post from its category in the DB
                        try: db["urgencies"][urgency].pop(db["urgencies"][urgency].index(postname))
                        except ValueError: pass
                    with open("db.json", "w") as dbfile:
                        dbfile.write(json.dumps(db))
                    return redirect(url_for('admin'))
                else:
                    abort(422)
            else:
                abort(422)
#
# NEW POST OR EDIT POST
#
    elif page in ["new", "edit"]:
        if page == "new" and argument != None: # new posts should not contain the argument
            abort(400)
        if page == "edit" and argument not in os.listdir("blogs/"): # only allow editing of pages which exist in the blogs dir, otherwise the edit functionality could possibly be used to make a post with any filename, which could mean arbitrary code execution, which is bad (duh).
            abort(404)

        if request.method == "GET":
            #
            # POST EDITOR (new mode)
            #
            if page == "new":
                return render_template("post_editor.html", mode="new", urgencies=db["urgencies"], all_categories=db["categories"])
            #
            # POST EDITOR (edit mode)
            #
            elif page == "edit":
                content = get_post_content(argument, "md")
                postinfo = get_post_info(argument)
                return render_template("post_editor.html", mode="edit", content=content, categories=postinfo["categories"], title=postinfo["title"], description=postinfo["description"], featured=db["featured"]==argument, urgencies=db["urgencies"], postimportance=postinfo["importance"])

        # here's where the real shit happens. takes the input from the post editors and actually does stuff with it (wow!). this stuff includes first determining if the request is a post or edit, putting the form data into a json file, and then putting the post content into a markdown file. it also handles making and/or editing all the necessary images.
        elif request.method == "POST":

            usednames = os.listdir("blogs/")
            if page == "new": # only run this if making a new post, because if we are editing we dont want to make a new file
                name_prefix = time.strftime("%m-%d-%Y", time.localtime(time.time()))
                count = 0
                while f"{name_prefix}-{count}" in usednames: count += 1 # makes a unique filename by counting up along the numbers after the date - which is set to server time.
                name = f"{name_prefix}-{count}"
                os.makedirs(f"blogs/{name}")
                author = username
                editors = []

            elif page == "edit": # only run if we are editing, preserves old name in url which is safe because we checked it against known safe filenames earlier
                if argument in usednames:
                    name = argument
                    postinfo = get_post_info(argument)
                    author = postinfo["author"]
                    editors = postinfo["editors"]
                    if username not in editors + [author]: editors.append(username)
                    for category in db["categories"]: # remove the post from its category in the DB
                        try: db["categories"][category].pop(db["categories"][category].index(name))
                        except ValueError: pass
                    for urgency in db["urgencies"]: # remove the post from its category in the DB
                        try: db["urgencies"][urgency].pop(db["urgencies"][urgency].index(name))
                        except ValueError: pass


                else: abort(418) # this sort of post request will only ever be sent if hackers be hacking - return teapot
            
            try: # encase everything that could have an effect on other pieces of data in a try so if it fails we can undo everything with minimal to no manual repair
                if not(request.form["importance"]) or not(request.form["title"]) or not(request.form["description"]):
                    abort(422)

                importance = request.form["importance"][:CONF_MAX_IMPORTANCE_NAME_LENGTH]

                count = 0
                categories = []
                categories_temp = []
                while True: # since we have the ability to put one post in many categories, we need to iterate over all form elements with the prefix category- and get their values, if we hit the except we know we've reached the end of the categories
                    try:
                        category = request.form[f"category-{count}"][:CONF_MAX_CATEGORY_NAME_LENGTH]
                        try:
                            if not name in db["categories"][category]: # if user puts the same category twice, dissallow that
                                db["categories"][category].append(name)
                        except KeyError: # sometimes the category doesnt exist, in that case we can make that category and assume the post isnt already in it (i spent 2 hours debugging this problem)
                            db["categories"][category] = []
                            db["categories"][category].append(name)

                        categories.append(category)
                        count += 1
                        if count > CONF_MAX_CATEGORIES_PER_POST: # ill add a rule on the frontend for this as well, but you can never trust user input
                            break
                    except KeyError:
                        if count == 0: abort(422)
                        else: break

                for cat in categories_temp:
                    db["categories"][cat].append(name)
                
                featured = False # default
                if "featured" in request.form: # featured is a checkbox, if it exists it's checked
                    db["featured"] = name
                    featured = True
                title = request.form["title"][:CONF_MAX_TITLE_LENGTH]
                
                if importance not in db["urgencies"]: # make the list so we can append to it
                    db["urgencies"][importance] = []
                db["urgencies"][importance].append(name) # TODO: make importance levels indexed from high to low so user can sort by importance

                description = request.form["description"][:CONF_MAX_DESCRIPTION_LENGTH]

                with open(f"blogs/{name}/db.json", "w") as postinfo:
                    postinfo.write(json.dumps({\
                        "title": title,\
                        "date": name,\
                        "importance": importance,\
                        "categories": categories,\
                        "description": description,\
                        "author": author,\
                        "editors": editors\
                    }))
                with open(f"blogs/{name}/page.md", "w") as post:
                    post.write(request.form["content"])

                with open("db.json", "w") as dbfile:
                    dbfile.write(json.dumps(db))
                
                # in case we are modifying any of these files, clear them from the cache. this just skips if the files arent in the cache so this is perfectly safe to just do every time
                read_cached.clear_entry(f"blogs/{name}/db.json")
                read_cached.clear_entry(f"blogs/{name}/page.md")

                if not os.path.exists(f"blogs/{name}/images"):
                    os.makedirs(f"blogs/{name}/images")

                # below code handles images
                banner = request.files["banner"]
                thumbnail = request.files["thumbnail"]
                favicon = request.files["favicon"]
                og = request.files["og"]
                
                bannerimg = False #set this for later
                if banner:
                    bannerimg = Image.open(banner.stream)
                    width, height = bannerimg.size
                    if width / height > 1920 / 640:
                        bannerimg = bannerimg.crop((0,\
                                (width-(width*(640/1920)))/2,\
                                width,\
                                ((width-(width*(640/1920)))/2) + (width*(640/1920))))
                    if width / height < 1920 / 640:
                        bannerimg = bannerimg.crop(((width-(height*(1920/640)))/2,\
                                0,\
                                ((width-(height*(1920/640)))/2) + (height*(1920/640)),\
                                height))
                    bannerimg = bannerimg.resize((1920, 640))
                elif not os.path.exists(f"blogs/{name}/images/banner.png"):
                    array = get_gradient_3d(1920, 640, (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)), (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)), (random.choice([True, False]), random.choice([True, False]), random.choice([True, False])))
                    bannerimg = Image.fromarray(np.uint8(array))
                if bannerimg:
                    bannerimg.save(f"blogs/{name}/images/banner.png")

                
                # TODO: make a cool page that shows confetti or something idk
                return "Post made sucessfully!"

            except: # deletes the post folder if something goes wrong, because an incomplete post folder causes errors
                # the or is a failsafe because im paranoid that if name isnt made for some reason itll delete the entire directory
                if page != "edit": shutil.rmtree(f"blogs/{name or 'SOMETHING HAS GONE TERRIBLY WRONG'}") 
                abort(500)
#
# ADMIN LOGIN
#
@app.route("/admin/login", methods=["GET", "POST"])
@limit_content_length(3 * 1024 * 1024) # if your username and password are larger than 3MB youre probably a bit too paranoid... this keeps people from uploading a terabyte of password and making the cpu try and hash all of that
def login():
    if request.method == "GET":
        return render_template("login.html")

    if request.method == "POST":
        try:
            hashedinputpass = hashlib.sha512(request.form["password"].encode("utf-8")).hexdigest()
            uname = request.form["username"]
            if hashedinputpass == users[uname]: # yay! login successful, set a cookie and continue to the admin dashboard
                while True:
                    random_id = base64.b64encode(os.urandom(256))
                    if random_id not in logged_in_db and random_id not in past_used_keys: # overlap is extremely unlikely, but nonetheless possible
                        break
                logged_in_db[random_id] = {"uname": uname, "last_access": time.time(), "initial_access": time.time(), "last_keepalive": time.time()}
                session['key'] = random_id
                return redirect("/admin", code=302)
            else:
                flash("Password incorrect!")
                return render_template("login.html", wrongpass=True)
        except KeyError: # if the username isnt in the dict, do this
            return render_template("login.html", wrongname=True)
#
# ADMIN LOGOUT
#
@app.route("/admin/logout", methods=["GET"])
def logout():
    logged_in_db.pop(session.pop("key", None)) # pop returns the user id, which gets popped from the DB
    return "Logged out!"



if __name__ == "__main__":
    app.secret_key = os.urandom(256) # overlap on user id _and_ key will only happen one every 13407807929942597099574024998205846127479365820592393377723561443721764030073546976801874298166903427690031858186486050853753882811946569946433649006084096 times (yes, i did the math). im willing to take those chances
    if CONF_DEBUG_ENABLE:
        from werkzeug.middleware.profiler import ProfilerMiddleware
        app.wsgi_app = ProfilerMiddleware(app.wsgi_app, restrictions=[20], profile_dir='./profile')
        app.run(debug=CONF_DEBUG_ENABLE)
    else:
        from waitress import serve
        if CONF_USE_SOCKET:
            serve(app,\
                  url_prefix=CONF_URL_PREFIX,\
                  unix_socket=CONF_UNIX_SOCKET,\
                  unix_socket_perms=CONF_UNIX_SOCKET_PERMS)

        else:
            serve(app,\
                  host=CONF_HOST,\
                  port=CONF_PORT,\
                  url_prefix=CONF_URL_PREFIX)

