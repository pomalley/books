from flask import Flask, g, session, redirect, url_for, request
from flask.ext.assets import Environment, Bundle
from flask.ext.sqlalchemy import SQLAlchemy
from mongokit import Connection

MONGODB_HOST = 'localhost'
MONGODB_PORT = 27017
MONGODB_DB = 'books'
MONGODB_COLLECTION = 'books'
T2_URL = '/t2/'
#SERVER_NAME = 'localhost:5000'
SERVER_NAME = 'tasker.physics.ucsb.edu'
APPLICATION_ROOT = 'books'

app = Flask(__name__)
app.config.from_object(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = \
                "postgresql://t2:rubypassword@localhost/t2_development"
app.secret_key = 'V\x1c\xd0\xc93\x9a7v\xbc\xa5\x1b\xaf[\xb77+\xed\xc7\xe8\t\xa0P\xba\x04'
app.worldcat_key = 'cl3HqQBWmmZqi5tmLZJsmpypsjOhfdLrefItvpOOSvzqWmmKZb5WCvXz8WU7RYM0FcREHG0goYHMpGvQ'
# config assets
assets = Environment(app)
#assets.url = app.static_url_path
scss = Bundle('books.scss', filters='pyscss', output='books.css')
assets.register('scss_all', scss)

db_auth = SQLAlchemy(app)

connection = Connection(app.config['MONGODB_HOST'],
                        app.config['MONGODB_PORT'])
db = connection[app.config['MONGODB_DB']]
collection = db[app.config['MONGODB_COLLECTION']]

import books.views
