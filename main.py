#!/usr/bin/env python3

# use http://www.patorjk.com/software/taag to make labels

from flask import Flask, render_template, abort, send_from_directory, session, redirect, request, flash, make_response
from markdown import markdown
from cachefiles import read_cached
from bs4 import BeautifulSoup
import json, hashlib, os, time, shutil

app = Flask(__name__)

site_name = "Plus ST Blog"

with open("db.json", "r") as dbfile:
    db = json.loads(dbfile.read())

with open("users.json", "r") as userdb:
    users = json.loads(userdb.read())


@app.route("/", methods=["GET"])
def homepage():

    def get_post_info(postname):
        #with open(f"blogs/{postname}/db.json") as postinfo:
        #    return json.loads(postinfo.read())
        return json.loads(read_cached(f"blogs/{postname}/db.json"))

    return render_template("index.html", \
            site_name = site_name,\
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

    if "." in postname or "/" in postname: # avoids any potential directory traversal
        abort(418)

    with open(f"blogs/{postname}/page.md") as source: # gets the HTML result from a post's MD file
        content = markdown(source.read(), extensions=['extra', 'codehilite', 'toc'])

    with open(f"blogs/{postname}/db.json") as postinfo:
        info = json.loads(postinfo.read())
 
    return render_template("page.html", content=content, title=info["title"], site_name=site_name)
#
# IMAGE HANDLER
#
@app.route("/posts/<postname>/images/<imgname>")
def serve_image(postname, imgname):
    return send_from_directory("blogs", f"{postname}/images/{imgname}")
#
# PLAINTEXT VIEWER
#
@app.route("/posts/<postname>/plaintext", methods=["GET"])
def viewpost_plaintext(postname):
    if "." in postname or "/" in postname: # avoids any potential directory traversal
        abort(418)

    soup = BeautifulSoup(markdown(read_cached(f"blogs/{postname}/page.md")), features='html.parser') # post (md) --> HTML --> beautifulsoup object
    response = make_response(soup.get_text(), 200) # turns the Beautifulsoup object into a response so we can give it a mimetype
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
def admin(page=None, argument=None):

    # nothing should return anything before this if statement, this controls the login
    username = session.get("username")
    if not username in users: # this redirects to the login page if the cookie does not exist or is tampered with
        return redirect("/admin/login", code=302)
#
# DASHBOARD
#
    elif page == None: # if no page is supplied, return the admin dashboard
        return render_template("admin.html", username=username)
#
# NEW POST OR EDIT POST
#
    elif page in ["new", "edit"]:
        if page == "new" and argument != None:
            abort(400)
        if page == "edit" and argument not in os.listdir("blogs/"):
            abort(404)

        if request.method == "GET":
            if page == "new":
                return render_template("post_editor.html", mode="new")
            elif page == "edit":
                if "." in argument or "/" in argument: # avoids any potential directory traversal
                    abort(418)
                content = read_cached(f"blogs/{argument}/page.md")
                return render_template("post_editor.html", mode="edit", content=content)


        elif request.method == "POST":
            usednames = os.listdir("blogs/")
            name_prefix = time.strftime("%m-%d-%Y", time.localtime(time.time()))
            count = 0
            while f"{name_prefix}-{count}" in usednames: count += 1
            name = f"{name_prefix}-{count}"
            os.makedirs(f"blogs/{name}")
            db["allposts"].append(name)
            
            try:
                featured = False
                if "featured" in request.form:
                    db["featured"] = name
                    featured = True

                count = 0
                categories = []
                while True:
                    try:
                        category = request.form[f"category-{count}"]
                        if category not in db["categories"]: 
                            db["categories"].append(category)
                        categories.append(category)
                        count += 1
                    except:
                        if count == 0:
                            abort(400)
                        break
            
                title = request.form["title"]

                importance = request.form["importance"] 
                if not importance in db["urgencies"]:
                    db["urgencies"][importance].append(name)

                description = request.form["description"]

                with open(f"blogs/{name}/db.json", "w") as postinfo:
                    postinfo.write(json.dumps({\
                        "title": title,\
                        "date": importance,\
                        "importance": importance,\
                        "categories": categories,\
                        "featured": featured,\
                        "description": description\
                    }))
                with open(f"blogs/{name}/page.md", "w") as post:
                    post.write(request.form["content"])

                with open("db.json", "w") as dbfile:
                    dbfile.write(json.dumps(db))

                return "Post made sucessfully!"

            except: # deletes the post folder if something goes wrong, because an incomplete post folder causes errors
                # the or is a failsafe because im paranoid that if name isnt made for some reason itll delete the entire directory
                shutil.rmtree(f"blogs/{name or 'SOMETHING HAS GONE TERRIBLY WRONG'}") 
                abort(500)
#
# ADMIN LOGIN
#
@app.route("/admin/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    if request.method == "POST":
        try:
            hashedinputpass = hashlib.sha512(request.form["password"].encode("utf-8")).hexdigest()
            uname = request.form["username"]
            if hashedinputpass == users[uname]:
                session['username'] = uname
                return redirect("/admin", code=302)
            else:
                flash("Password incorrect!")
                return render_template("login.html", wrongpass=True)
        except KeyError:
            return render_template("login.html", wrongname=True)
#
# ADMIN LOGOUT
#
@app.route("/admin/logout", methods=["get"])
def logout():
    session.pop("username", None)
    return "Logged out!"



if __name__ == "__main__":
    # Only enable for debugging
    # from werkzeug.middleware.profiler import ProfilerMiddleware
    # app.wsgi_app = ProfilerMiddleware(app.wsgi_app, restrictions=[5], profile_dir='./profile')

    app.secret_key = os.urandom(48)
    app.run(debug=True)
