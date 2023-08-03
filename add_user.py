#!/usr/bin/env python3
import re, json, hashlib, os
from getpass import getpass
import secrets

if not os.path.exists("users.json"):
    open("users.json", "w").close()

with open("users.json", "r+") as users:
    try: userlist = json.loads(users.read())
    except json.decoder.JSONDecodeError: userlist = {}
    
    username = input("Enter a username (only characters: a-z A-Z 0-9 . _ - max length 15 chars)\n\n--> ")
    reg = re.compile("^[a-zA-Z 0-9\.\_\-]*$")

    while not reg.match(username) or len(username) > 15 or username in userlist:
        if username in userlist:
            if input("User already exists! change password? [Y/n]").upper() in ["Y", "YES", ""]: break
            else: print("Please enter a different username.")
        else:
            print("Your username does not fit the constraints, please try again.")
        username = input("Enter a username (only characters: a-z A-Z 0-9 . _ -)\n\n--> ")
    
    password = getpass("Enter a strong password: ")
    while password != getpass("Confirm password: "):
        print("Passwords do not match, try again!")
        password = getpass("Enter a strong password: ")
    
    salt = secrets.token_hex(8)
    password += salt
    password = hashlib.sha512(password.encode("utf-8")).hexdigest()

    print("Please select a role:")
    roles = {"1": "admin", "2": "user"}
    for role in roles: print(f"{role}.) {roles[role]}")
    while True:
        userinput = input("\n--> ")
        try:
            userrole = roles[userinput]
            break
        except KeyError:
            print(f"Please select from {[i for i in roles]}")
    userlist[username] = {"passhash":password, "salt":salt, "role":userrole}

    users.seek(0) # write from start of file so it doesnt just add to the end of it
    users.write(json.dumps(userlist) + "\n")
    users.truncate()
