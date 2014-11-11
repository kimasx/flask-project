import os
from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.login import LoginManager
from flask.ext.openid import OpenID
from config import basedir



# create the application object of class Flask
app = Flask(__name__)

# read and use our config file
app.config.from_object('config')

# initialise our database
db = SQLAlchemy(app)

lm = LoginManager()
lm.init_app(app)
lm.login_view = 'login'

# Flask-OpenID ext requres a path to a temp folder where files can be stored
oid = OpenID(app, os.path.join(basedir, 'tmp'))

from app import views, models