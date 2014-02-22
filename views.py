import functools, urllib

from flask import abort, g, render_template, url_for, session, flash, redirect, request, make_response

from flask.ext.classy import route
from flask_wtf import Form
import wtforms, wtforms.validators as validators

from books import app, auth
from book import Book

class LoginForm(Form):
    username = wtforms.TextField('Username', validators=[validators.Required()])
    password = wtforms.PasswordField("Password", validators=[validators.Required()])

#---- the routes ----#

@app.before_request
def check_login():
    try:
        token = request.cookies.get('remember_token', '')
        g.user = auth.current_user(token)
    except KeyError:
        g.user = None

def login_required(f):
    @functools.wraps(f)
    def func(*args, **kwargs):
        if g.get('user', None) is None:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return func


# "static" routes here. see book module for routes based on books
@app.route('/')
@login_required
def index():
    return render_template("index.html")

@app.route("/site-map")
def site_map():
    return str(request.cookies)
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
