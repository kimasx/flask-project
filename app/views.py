from app import app

# render_template func takes a template filename & a variable list of temp. args.
from flask import render_template, flash, redirect

# import LoginForm class from forms.py
from .forms import LoginForm

# map index function to routes
@app.route('/')
@app.route('/index')
def index():
	user = {'nickname': 'Sun'}
	posts = [
		{
			'author': {'nickname': 'Jay'},
			'body': 'Nice day in NYC'
		},
		{
			'author': {'nickname': 'Susan'},
			'body': 'Interstellar was a good film!'
		}
	]

	return render_template('index.html', user=user, posts=posts)

@app.route('/login', methods=['GET', 'POST'])
def login():
	# instantiate a form object from LoginForm class
	form = LoginForm()
	# validate_on_submit first returns False when presenting form to user
	# when form submission request is made, the function runs all validators
	# and return True if everything is all right
	if form.validate_on_submit():
		# flash shows message to user
		flash('Login requested for OpenID="%s", remember_me=%s' %
			(form.openid.data, str(form.remember_me.data)))
		return redirect('/index')

	return render_template('login.html', title='Sign In', form=form, providers=app.config['OPENID_PROVIDERS'])