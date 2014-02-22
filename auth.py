''' auth.py

auth stuff for books. we use the same (literally) auth as for t2. '''

import hashlib, os, base64, functools

from books import app, db_auth as db, session

class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    email = db.Column(db.String)
    password_digest = db.Column(db.String)
    remember_token = db.Column(db.String)
    admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime)

def auth(user, password):
    return True

def encrypt(token):
    return hashlib.sha1(token).hexdigest()

def new_remember_token():
    return base64.b64encode(os.urandom(16))

def current_user(token):
    # look up hashed remember token in the (ruby) db
    return Users.query.filter_by(remember_token=encrypt(token)).first()
