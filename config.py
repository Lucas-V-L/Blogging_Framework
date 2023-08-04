# This is just a simple python script that gets imported when the program starts, make sure to follow proper python syntax and dont delete or make any new variables or youll fuck up the server.

CONF_SITE_NAME = "Blogging Framework" # set this to your site name, gets used in the page title and such
CONF_MAX_CATEGORIES_PER_POST = 10 # this and the following line are important to understand, having a long category length and high category count will increase the size of those categories on the page exponentially because they multiply eachother
CONF_MAX_CATEGORY_NAME_LENGTH = 20 
CONF_MAX_TITLE_LENGTH = 80
CONF_MAX_IMPORTANCE_NAME_LENGTH = 15 # shouldnt be too long to prevent formatting issues
CONF_MAX_DESCRIPTION_LENGTH = 200 # shouldnt be too long to prevent formatting issues
CONF_MAX_COMMENT_LENGTH = 250 # max length for comments on posts to be
CONF_STAY_LOGGED_IN_DURATION = 60 * 60 # 1 hour - resets on refresh
CONF_TOTAL_STAY_LOGGED_IN_DURATION = 60 * 60 * 24 * 3 # 3 days - if the user has been logged in for longer than this amount of time, they will be logged out no matter what unless keepalive keeps the user logged in
CONF_ENABLE_LOGIN_KEEPALIVE = True # login keepalive allows the max total stay logged in duration to be extended by 120 seconds every 110 seconds. this happens automatically on the post editor page to ensure a logout does not occur while a post is being edited before it can be saved
CONF_DEBUG_ENABLE = True # turn this on in production for free vbux, totally wont allow remote code execution on your server :)
CONF_HOST = "127.0.0.1" # if the unix socket is disabled the server will listen on this interface
CONF_USE_SOCKET = False
CONF_UNIX_SOCKET = "./socket.sock"
CONF_UNIX_SOCKET_PERMS = "777" # please restrict this, i have it set 777 for debugging and because im lazy, it should never be this in production
CONF_PORT = 8080 # port to listen on
CONF_URL_PREFIX = "" # if behind a reverse proxy at say example.com/blog, set this to "blog", otherwise leave it be
CONF_OG_IMG_FONT = "/usr/share/fonts/adobe-source-code-pro/SourceCodePro-BlackIt.otf" # path to the font for the og:image
CONF_OG_IMG_FONT_SIZE = 50 # font size for the og:image when text is overlaid on the banner image, if you have really long titles then make this smaller but otherwise just keep it as is
CONF_ALLOWED_FILETYPES = [".png", ".jpg", ".jpeg", ".pdf", ".zip", ".tar.gz"] # highly advise against adding executables, not really for user safety, but because inevitably some asshole will get them to run on the server
