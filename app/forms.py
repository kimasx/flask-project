from flask.ext.wtf import Form
from wtforms import StringField, BooleanField
# DataRequired is a validator that checks that the field submitted is not empty
from wtforms.validators import DataRequired

class LoginForm(Form):
	# requires openid string to login
	openid = StringField('openid', validators=[DataRequired()])
	# installs a cookie in the browser so it remembers login
	remember_me = BooleanField('remember_me', default=False)