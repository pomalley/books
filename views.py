import urllib

from flask import abort, g, render_template, url_for, session, flash, redirect, request, make_response

from . import app
from book import Book
from bread import Bread
from view_helpers import login_required
import auth

#---- the routes ----#

@app.before_request
def check_login():
    try:
        token = request.cookies.get('remember_token', '')
        g.user = auth.current_user(token)
    except KeyError:
        g.user = None


# "static" routes here. see book module for routes based on books
@app.route('/')
def index():
    return render_template("index.html")

@app.route("/site-map")
@login_required
def site_map():
    links = []
    for rule in app.url_map.iter_rules():
        links.append(rule.endpoint + ' ' + str(rule))
    return '<br>'.join(links)

@app.route('/login', methods=["GET", "POST"])
def login(next=None):
    next = next or request.referrer or url_for('index', _external=True)
    url = app.config['T2_URL'] + 'signin/?next=%s' % urllib.quote(next)
    return redirect(url)

@app.route('/logout')
def logout(next=None):
    g.user = None
    url = next or request.referrer or url_for('index')
    resp = make_response(redirect(url))
    resp.set_cookie('remember_token', '', expires=0)
    return resp

@app.template_global(name='zip')
def _zip(*args, **kwargs): #to not overwrite builtin zip in globals
    return __builtins__['zip'](*args, **kwargs)

# the main routes come from the Book model
Book.getView().register(app)
Bread.getView().register(app)
