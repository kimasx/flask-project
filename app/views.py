# render_template func takes a template filename & a variable list of temp. args.
from flask import render_template, flash, redirect, session, url_for, request, g
from flask.ext.login import login_user, logout_user, current_user, login_required
from app import app, db, lm, oid

# import LoginForm class from forms.py
from forms import LoginForm, EditForm
from models import User
from datetime import datetime


# loads a user from the database
@lm.user_loader
def load_user(id):
	return User.query.get(int(id))	


# map index function to routes
@app.route('/')
@app.route('/index')
@login_required # this ensures that the index page is seen only by logged in users
def index():
	user = g.user
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

# set g.user var to the current_user global
@app.before_request
def before_request():
	g.user = current_user
	# update time in db each time browser makes a request
	if g.user.is_authenticated():
		g.user.last_seen = datetime.utcnow()
		db.session.add(g.user)
		db.session.commit


@app.route('/login', methods=['GET', 'POST'])
@oid.loginhandler # tells flask-openid that this is our login view function
def login():
	# 'g' is a global where flask stores the logged in user
	# here we check if g.user is set to authenticated user and redirect to index page if so.
	if g.user is not None and g.user.is_authenticated():
		return redirect(url_for('index'))
	# instantiate a form object from LoginForm class
	form = LoginForm()
	# validate_on_submit first returns False when presenting form to user
	# when form submission request is made, the function runs all validators
	# and return True if everything is all right
	if form.validate_on_submit():
		# store 'remember_me' value in session, where the data stored is available during current and future requests 
		session['remember_me'] = form.remember_me.data
		# triggers user auth. thru openid
		return oid.try_login(form.openid.data, ask_for=['nickname', 'email'])
	return render_template('login.html', title='Sign In', form=form, providers=app.config['OPENID_PROVIDERS'])


@oid.after_login
def after_login(resp):	# resp is arg that contains info returned by openid provider
	if resp.email is None or resp.email == '':
		flash('Invalid Login. Try again.')
		return redirect(url_for('login'))
	# search db for the email provided
	user = User.query.filter_by(email=resp.email).first()
	# add new user if email not found
	if user is None:
		nickname = resp.nickname
		if nickname is None or nickname == '':
			nickname = resp.email.split('@')[0]
		user = User(nickname=nickname, email=resp.email)
		db.session.add(user)
		db.session.commit()
	remember_me = False
	# load remember_me value from flask session
	if 'remember_me' in session:
		remember_me = session['remember_me']
		session.pop('remember_me', None)
	login_user(user, remember=remember_me)
	return redirect(request.args.get('next') or url_for('index'))


@app.route('/logout')
def logout():
	logout_user()
	return redirect(url_for('index'))


@app.route('/user/<nickname>')
@login_required
def user(nickname):
	user = User.query.filter_by(nickname=nickname).first()	# load user from db
	if user == None:
		flash('User %s not found.' % nickname)
		return redirect(url_for('index'))
	posts = [
		{'author': user, 'body': 'Text post #1'},
		{'author': user, 'body': 'Test post #2'}
	]
	return render_template('user.html', user=user, posts=posts)


@app.route('/edit', methods=['GET', 'POST'])
@login_required
def edit():
	form = EditForm()
	if form.validate_on_submit():
		g.user.nickname = form.nickname.data
		g.user.about_me = form.about_me.data
		db.session.add(g.user)
		db.session.commit()
		flash('Changes saved!')
		return redirect(url_for('edit'))
	else:
		form.nickname.data = g.user.nickname
		form.about_me.data = g.user.about_me
	return render_template('edit.html', form=form)









