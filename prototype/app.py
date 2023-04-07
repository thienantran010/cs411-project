# Python standard libraries
import json
import os
import sqlite3

# Third party libraries
from flask import Flask, redirect, request, url_for, render_template
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
)
from oauthlib.oauth2 import WebApplicationClient
import requests
import random

# Internal imports
from db import init_db_command
from user import User
from config import client_id, client_secret, app_secret_key

# Configuration
GOOGLE_CLIENT_ID = client_id
GOOGLE_CLIENT_SECRET = client_secret
GOOGLE_DISCOVERY_URL = (
    "https://accounts.google.com/.well-known/openid-configuration"
)

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
QUOTES_BASE_URL = "https://api.quotable.io"
WAIFU_PICS_BASE_URL = "https://api.waifu.pics"
MEME_MAKER_BASE_URL = 'https://api.memegen.link/images/custom'

# Flask app setup
app = Flask(__name__)
app.secret_key = app_secret_key

# User session management setup
# https://flask-login.readthedocs.io/en/latest
login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.unauthorized_handler
def unauthorized():
    return "You must be logged in to access this content.", 403


# Naive database setup
try:
    init_db_command()
except sqlite3.OperationalError:
    # Assume it's already been created
    pass

# OAuth2 client setup
client = WebApplicationClient(GOOGLE_CLIENT_ID)


# Flask-Login helper to retrieve a user from our db
@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

def get_id_from_email(email):
    con = sqlite3.connect("sqlite_db")
    cur = con.cursor()
    cur.execute("SELECT id FROM user WHERE email = ?", (email,))

    # fetch the result. The result is a tuple so we extract the id from the tuple
    id = cur.fetchone()[0]

    con.close()
    return id

def get_memes_from_email(email):
    id = get_id_from_email(email)
    con = sqlite3.connect("sqlite_db")
    cur = con.cursor()
    cur.execute("SELECT url FROM meme WHERE id = ?", (id,))

    # fetchall() returns a list of tuples
    results = cur.fetchall()

    # Extracting the meme urls from the tuples
    meme_urls = [meme_url for (meme_url,) in results]
    con.close()
    return meme_urls

################################################################
@app.route("/")
def index():
    if current_user.is_authenticated:
        meme_urls = get_memes_from_email(current_user.email)
        return render_template('profile.html', name=current_user.name, email=current_user.email, 
                               profile_pic_url=current_user.profile_pic, meme_urls=meme_urls)
        return (
            "<p>Hello, {}! You're logged in! Email: {}</p>"
            "<div><p>Google Profile Picture:</p>"
            '<img src="{}" alt="Google profile pic"></img></div>'
            '<a class="button" href="/logout">Logout</a>'.format(
                current_user.name, current_user.email, current_user.profile_pic
            )
        )
    else:
        return '<a class="button" href="/login">Google Login</a>'
##################################################################

@app.route("/login")
def login():
    # Find out what URL to hit for Google login
    google_provider_cfg = get_google_provider_cfg()
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]

    # Use library to construct the request for login and provide
    # scopes that let you retrieve user's profile from Google
    request_uri = client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri=request.base_url + "/callback",
        scope=["openid", "email", "profile"],
    )
    return redirect(request_uri)


@app.route("/login/callback")
def callback():
    # Get authorization code Google sent back to you
    code = request.args.get("code")

    # Find out what URL to hit to get tokens that allow you to ask for
    # things on behalf of a user
    google_provider_cfg = get_google_provider_cfg()
    token_endpoint = google_provider_cfg["token_endpoint"]

    # Prepare and send request to get tokens! Yay tokens!
    token_url, headers, body = client.prepare_token_request(
        token_endpoint,
        authorization_response=request.url,
        redirect_url=request.base_url,
        code=code,
    )
    token_response = requests.post(
        token_url,
        headers=headers,
        data=body,
        auth=(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET),
    )

    # Parse the tokens!
    client.parse_request_body_response(json.dumps(token_response.json()))

    # Now that we have tokens (yay) let's find and hit URL
    # from Google that gives you user's profile information,
    # including their Google Profile Image and Email
    userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
    uri, headers, body = client.add_token(userinfo_endpoint)
    userinfo_response = requests.get(uri, headers=headers, data=body)

    # We want to make sure their email is verified.
    # The user authenticated with Google, authorized our
    # app, and now we've verified their email through Google!
    if userinfo_response.json().get("email_verified"):
        unique_id = userinfo_response.json()["sub"]
        users_email = userinfo_response.json()["email"]
        picture = userinfo_response.json()["picture"]
        users_name = userinfo_response.json()["given_name"]
    else:
        return "User email not available or not verified by Google.", 400

    # Create a user in our db with the information provided
    # by Google
    user = User(
        id_=unique_id, name=users_name, email=users_email, profile_pic=picture
    )

    # Doesn't exist? Add to database
    if not User.get(unique_id):
        User.create(unique_id, users_name, users_email, picture)

    # Begin user session by logging the user in
    login_user(user)

    # Send user back to homepage
    return redirect(url_for("index"))

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))

def get_google_provider_cfg():
    return requests.get(GOOGLE_DISCOVERY_URL).json()

# removed 'athletics' and 'proverb' because they didn't work
quotes_tags = ['business', 'change', 'character', 'competition', 'conservative', 'courage', 
               'education', 'faith', 'family', 'famous-quotes', 'film', 'freedom', 'friendship', 'future', 
               'happiness', 'history', 'honor', 'humor', 'humorous', 'inspirational', 'leadership', 'life', 
               'literature', 'love', 'motivational', 'nature', 'pain', 'philosophy', 'politics', 'power-quotes', 
               'religion', 'science', 'self', 'self-help', 'social-justice', 'spirituality', 'sports', 
               'success', 'technology', 'time', 'truth', 'virtue', 'war', 'wisdom']

image_categories = ["waifu", "neko", "shinobu", "megumin", "bully", "cuddle", "cry", "hug", "awoo", "kiss", 
                    "lick", "pat", "smug", "bonk", "yeet", "blush", "smile", "wave", "highfive", "handhold", 
                    "nom", "bite", "glomp", "slap", "kill", "kick", "happy", "wink", "poke", "dance", "cringe"]
########################################################
@app.route("/createMeme", methods=['POST', 'GET'])
@login_required
def createMeme():
    if request.method == 'POST':
        tag = request.form.get('tag')
        print(tag)
        random_quote_url = f"{QUOTES_BASE_URL}/random?tags={tag}"
        response = requests.get(random_quote_url).json()
        quote = response['content']
        image_category = random.choice(image_categories)
        random_image_url = f"{WAIFU_PICS_BASE_URL}/sfw/{image_category}"
        response = requests.get(random_image_url).json()
        image_url = response['url']
        body = {
        "background": image_url,
        "text": [
            quote
        ],
        "layout": "top",
        "font": "notosans",
        "extension": "jpg",
        }
        response = requests.post(MEME_MAKER_BASE_URL, json=body)
        meme = response.json()
        meme_url = meme['url']

        con = sqlite3.connect("sqlite_db")
        cur = con.cursor()
        user_id = get_id_from_email(current_user.email)
        cur.execute("INSERT INTO meme (id, url) VALUES (?, ?)", (user_id, meme_url))
        con.commit()
        con.close()

        return render_template('meme.html', url=meme_url)
    else:
        return render_template('createMeme.html', tags=quotes_tags)
########################################################


if __name__ == "__main__":
    app.run(debug=True)
