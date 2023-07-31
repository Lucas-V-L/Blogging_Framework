# This is just a simple python script that gets imported when the program starts, make sure to follow proper python syntax and dont delete any variables or youll fuck up the server

CONF_SITE_NAME = "Blogging Framework"
CONF_MAX_CATEGORIES_PER_POST = 10
CONF_MAX_CATEGORY_NAME_LENGTH = 20
CONF_MAX_TITLE_LENGTH = 50
CONF_MAX_IMPORTANCE_NAME_LENGTH = 15
CONF_MAX_DESCRIPTION_LENGTH = 200
CONF_STAY_LOGGED_IN_DURATION = 60 * 60 # 1 hour - resets on refresh
CONF_TOTAL_STAY_LOGGED_IN_DURATION = 60 * 60 * 24 * 3 # 3 days - if the user has been logged in for longer than this amount of time, they will be logged out no matter what unless keepalive keeps the user logged in
CONF_ENABLE_LOGIN_KEEPALIVE = True # login keepalive allows the max total stay logged in duration to be extended by 120 seconds every 110 seconds. this happens automatically on the post editor page to ensure a logout does not occur while a post is being edited before it can be saved
CONF_DEBUG_ENABLE = True
CONF_HOST = "127.0.0.1"
CONF_USE_SOCKET = False
CONF_UNIX_SOCKET = "./socket.sock"
CONF_UNIX_SOCKET_PERMS = "777"
CONF_PORT = 8080
CONF_URL_PREFIX = ""
