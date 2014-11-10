from flask import Flask

# create the application object of class Flask
app = Flask(__name__)

# read and use our config file
app.config.from_object('config')

# import views module
from app import views