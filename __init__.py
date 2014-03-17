from flask import Flask, g, session, redirect, url_for, request
from flask.ext.assets import Environment, Bundle
from flask.ext.sqlalchemy import SQLAlchemy
from mongokit import Connection

import os
import config

import private

app = Flask(__name__)
app.secret_key = private.secret_key
config.DevelopmentConfig.SQLALCHEMY_DATABASE_URI = private.dev_sql_database
config.ProductionConfig.SQLALCHEMY_DATABASE_URI = private.prod_sql_database


env = os.environ['FLASK_BOOKS_ENV'].lower()
if env == 'dev' or env == 'development':
    app.config.from_object(config.DevelopmentConfig)
elif env == 'prod'or env == 'production':
    app.config.from_object(config.ProductionConfig)
else:
    raise RuntimeError("environment variable FLASK_BOOKS_ENV not set to dev or prod.")



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
