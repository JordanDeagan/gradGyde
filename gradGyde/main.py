import os
from flask import render_template, request, session, url_for
from flask_oauthlib.client import OAuth, redirect
from gradGyde import app
from .db_helper import DatabaseHelper
from .models import UserType

DBHELPER = DatabaseHelper()
OAUTH = OAuth()
GOOGLE = OAUTH.remote_app('google',
                          consumer_key=os.getenv('GOOGLE_CONS_KEY'),
                          consumer_secret=os.getenv('GOOGLE_CONS_SECRET'),
                          request_token_params={'scope': 'email'},
                          base_url='https://www.googleapis.com/oauth2/v1/',
                          request_token_url=None,
                          access_token_method='POST',
                          access_token_url='https://accounts.google.com/o/oauth2/token',
                          authorize_url='https://accounts.google.com/o/oauth2/auth')


@GOOGLE.tokengetter
def get_google_token():
    return session.get("google_token")


@app.route('/')
def index():
    return "hello world"

@app.route('/test')
def test():
    return "test"

@app.route('/oauth_google')
def oauth_google():
    return GOOGLE.authorize(callback=url_for('oauth_google_authorized',
                                             _external=True))


@app.route('/authorized/')
def oauth_google_authorized():
    resp = GOOGLE.authorized_response()
    if resp is None:
        return 'Google denied access. Reason: %s \n Error: %s' %(
            request.args['error_reason'],
            request.args['error_description'])
    session['google_token'] = (resp['access_token'], '')
    user_info = GOOGLE.get('userinfo').data
    session['google_user'] = user_info
    session['user_name'] = session['google_user']['email']
    session['user'] = DBHELPER.get_user(session['user_name'])
    if session['user'] is None:
        return redirect('/signup_form')   
    return redirect('/student_dashboard')

@app.route('/login')
def login():
    return render_template('login.html')


@app.route('/logout')
def oauth_logout():
    session.pop('google_token', None)
    session['google_user'] = None
    session['user_name'] = None
    return redirect('/login')


@app.route('/signup_form')
def signup_form():
    if 'google_token' not in session:
        return "Log in to see this page!"
    #Change these to pull from the database
    aoc = ['Wizardry',
           'Computer Science',
           'General Studies',
           'Underwater Basket Weaving',
           'Biology']
    return render_template('signup_form.html',
                           aocs=aoc,
                           slashs=aoc,
                           doubles=aoc)


@app.route('/signup_form/post', methods=['POST'])
def signup_form_submit():
    if 'google_token' not in session:
        return "Log in to see this page!"
    name = request.form['name']
    aoc = request.form.getlist('AOC')
    slash = request.form.getlist('slash')
    da_year = request.form['year']
    DBHELPER.make_user(session['user_name'], name, da_year, UserType.STUDENT)
    session['user'] = DBHELPER.get_user(session['user_name'])
    return redirect('/student_dashboard')

@app.route('/student_dashboard')
def dash_stud():
    if 'google_token' not in session:
        return "Log in to see this page!"
    return render_template('dash_stud.html')
