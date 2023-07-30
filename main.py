#!/usr/bin/env python3

# use http://www.patorjk.com/software/taag to make labels

from flask import Flask, render_template, abort, send_from_directory, session, redirect, request, flash, make_response
from misc_functions import read_cached, get_post_content, get_post_info, limit_content_length
import json, hashlib, os, time, shutil, base64

app = Flask(__name__)


# TODO: put this in a config file
CONF_SITE_NAME = "Blogging Framework"
CONF_MAX_CATEGORIES_PER_POST = 10
CONF_MAX_CATEGORY_NAME_LENGTH = 20
CONF_MAX_TITLE_LENTH = 50
CONF_MAX_IMPORTANCE_NAME_LENGTH = 15
CONF_MAX_DESCRIPTION_LENTH = 200
CONF_STAY_LOGGED_IN_DURATION = 60 # 1 minute - resets on refresh
CONF_TOTAL_STAY_LOGGED_IN_DURATION = 120 # 10 minutes - if the user has been logged in for longer than this amount of time, they will be logged out no matter what
CONF_ENABLE_LOGIN_KEEPALIVE = True # login keepalive allows the max total stay logged in duration to be extended by 120 seconds every 110 seconds. this happens automatically on the post editor page to ensure a logout does not occur while a post is being edited before it can be saved
CONF_DEBUG_ENABLE = True


with open("db.json", "r") as dbfile:
    db = json.loads(dbfile.read())

with open("users.json", "r") as userdb:
    users = json.loads(userdb.read())

logged_in_db = {}

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
# MAIN PAGES
#
@app.route("/admin/<page>/<argument>", methods=["GET", "POST"])
@app.route("/admin/<page>", methods=["GET", "POST"])
@app.route("/admin", methods=["GET"])
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
    if page == "login-keepalive" and CONF_ENABLE_LOGIN_KEEPALIVE: # adds time to initial access, but rate limited. this is so that a script on the editor page can keep the user from being logged out before they can save their work.
        if time.time() - logged_in_db[user_id]["last_keepalive"] > 110: 
            logged_in_db[user_id]["initial_access"] += 120
            logged_in_db[user_id]["last_keepalive"] = time.time()
            return ('', 204)
        else: abort(429)
#
# DASHBOARD
#
    if page == None: # if no page is supplied, return the admin dashboard
        return render_template("admin.html", username=username)
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
                return render_template("post_editor.html", mode="new", urgencies=db["urgencies"])
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
                name_prefix = time.strftime("%m-%d-%Y", time.localtime(time.time())) # TODO: in the future i plan on having this change based on a timezone the browser sends, but for now this works
                count = 0
                while f"{name_prefix}-{count}" in usednames: count += 1 # makes a unique filename by counting up along the numbers after the date - which is set to server time.
                name = f"{name_prefix}-{count}"
                os.makedirs(f"blogs/{name}")
                db["allposts"].append(name)
            elif page == "edit": # only run if we are editing, preserves old name in url which is safe because we checked it against known safe filenames earlier
                if argument in usednames:
                    name = argument
            
            try: # encase everything that could have an effect on other pieces of data in a try so if it fails we can undo everything with minimal to no manual repair
                featured = False # default
                if "featured" in request.form: # featured is a checkbox, if it exists it's checked
                    db["featured"] = name
                    featured = True

                count = 0
                categories = []
                while True: # since we have the ability to put one post in many categories, we need to iterate over all form elements with the prefix category- and get their values, if we hit the except we know we've reached the end of the categories
                    try:
                        category = request.form[f"category-{count}"][:CONF_MAX_CATEGORY_NAME_LENGTH]
                        if category not in db["categories"]: # if the user makes a new category, add it to the list of categories
                            db["categories"].append(category)
                        categories.append(category)
                        count += 1
                        if count > CONF_MAX_CATEGORIES_PER_POST: # ill add a rule on the frontend for this as well, but you can never trust user input
                            break
                    except:
                        if count == 0:
                            abort(400)
                        break
            
                title = request.form["title"][:CONF_MAX_TITLE_LENGTH]

                importance = request.form["importance"][:CONF_MAX_IMPORTANCE_NAME_LENGTH]
                if not importance in db["urgencies"]:
                    db["urgencies"][importance].append(name) # TODO: make importance levels indexed from high to low so user can sort by importance

                description = request.form["description"][:CONF_MAX_DESCRIPTION_LENGTH]

                with open(f"blogs/{name}/db.json", "w") as postinfo:
                    postinfo.write(json.dumps({\
                        "title": title,\
                        "date": name,\
                        "importance": importance,\
                        "categories": categories,\
                        "description": description\
                    }))
                with open(f"blogs/{name}/page.md", "w") as post:
                    post.write(request.form["content"])

                with open("db.json", "w") as dbfile:
                    dbfile.write(json.dumps(db))
                
                # in case we are modifying any of these files, clear them from the cache. this just skips if the files arent in the cache so this is perfectly safe to just do every time
                read_cached.clear_entry(f"blogs/{name}/db.json")
                read_cached.clear_entry(f"blogs/{name}/page.md")
                
                # TODO: make a cool page that shows confetti or something idk
                return "Post made sucessfully!"

            except: # deletes the post folder if something goes wrong, because an incomplete post folder causes errors
                # the or is a failsafe because im paranoid that if name isnt made for some reason itll delete the entire directory
                shutil.rmtree(f"blogs/{name or 'SOMETHING HAS GONE TERRIBLY WRONG'}") 
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
                    if random_id not in logged_in_db:
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
    if CONF_DEBUG_ENABLE:
        from werkzeug.middleware.profiler import ProfilerMiddleware
        app.wsgi_app = ProfilerMiddleware(app.wsgi_app, restrictions=[20], profile_dir='./profile')

    app.secret_key = os.urandom(256)
    app.run(debug=CONF_DEBUG_ENABLE)
