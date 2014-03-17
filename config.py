''' config.py

config info for flask/books
'''

class Config(object):
    MONGODB_HOST = 'localhost'
    MONGODB_PORT = 27017
    MONGODB_DB = 'books'
    MONGODB_COLLECTION = 'books'
    #WORLDCAT_KEY = 'cl3HqQBWmmZqi5tmLZJsmpypsjOhfdLrefItvpOOSvzqWmmKZb5WCvXz8WU7RYM0FcREHG0goYHMpGvQ'

class DevelopmentConfig(Config):
    T2_URL = 'http://localhost:3000/'
    SERVER_NAME = 'localhost:5000'
    #SQLALCHEMY_DATABASE_URI =

class ProductionConfig(Config):
    T2_URL = '/t2/'
    SERVER_NAME = 'tasker.physics.ucsb.edu'
    #SQLALCHEMY_DATABASE_URI =
