# render_template func takes a template filename & a variable list of temp. args.
from flask import render_template, flash, redirect, session, url_for, request, g
from flask.ext.login import login_user, logout_user, current_user, login_required
from app import app, db, lm, oid

# import LoginForm class from forms.py
from forms import LoginForm, EditForm, PostForm, SearchForm
from .models import User, Post
from datetime import datetime
from config import POSTS_PER_PAGE, MAX_SEARCH_RESULTS


# loads a user from the database
@lm.user_loader
def load_user(id):
	return User.query.get(int(id))	

# set g.user var to the current_user global
@app.before_request
def before_request():
	g.user = current_user
	# update time in db each time browser makes a request
	if g.user.is_authenticated():
		g.user.last_seen = datetime.utcnow()
		db.session.add(g.user)
		db.session.commit()
		g.search_form = SearchForm()


# error handling
@app.errorhandler(404)
def not_found_error(error):
	return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
	db.session.rollback()
	return render_template('500.html'), 500


# map index function to routes
@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
@app.route('/index/<int:page>', methods=['GET', 'POST'])
@login_required # this ensures that the index page is seen only by logged in users
def index(page=1):
	form = PostForm()
	if form.validate_on_submit():
		post = Post(body=form.post.data, timestamp=datetime.utcnow(), author=g.user)
		db.session.add(post)
		db.session.commit()
		flash('Your post is now live!')
		return redirect(url_for('index'))
	posts = g.user.followed_posts().paginate(page, POSTS_PER_PAGE, False)	# this query returns obj that grabs the posts we are looking for
	return render_template('index.html', title='Home', form=form, posts=posts)



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


# called when a user successfully logs in to the system
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
		nickname = User.make_unique_nickname(nickname)
		user = User(nickname=nickname, email=resp.email)
		db.session.add(user)
		db.session.commit()
		# all users will follow him/herself
		db.session.add(user.follow(user))
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
@app.route('/user/<nickname>/<int:page>')
@login_required
def user(nickname, page=1):
	user = User.query.filter_by(nickname=nickname).first()	# load user from db
	if user == None:
		flash('User %s not found.' % nickname)
		return redirect(url_for('index'))
	posts = user.posts.paginate(page, POSTS_PER_PAGE, False)
	return render_template('user.html', user=user, posts=posts)


@app.route('/edit', methods=['GET', 'POST'])
@login_required
def edit():
	form = EditForm(g.user.nickname)
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


@app.route('/follow/<nickname>')
@login_required
def follow(nickname):
	user = User.query.filter_by(nickname=nickname).first()
	if user is None:
		flash('User %s is not found.' % nickname)
		return redirect(url_for('index'))
	if user == g.user:
		flash('You can\'t follow yourself')
		return redirect(url_for('user', nickname=nickname))
	u = g.user.follow(user)
	if u is None:
		flash('Cannot follow ' + nickname)
		return redirect(url_for('user', nickname=nickname))
	db.session.add(u)
	db.session.commit()
	flash('You are now following ' + nickname)
	return redirect(url_for('user', nickname=nickname))


@app.route('/unfollow/<nickname>')
@login_required
def unfollow(nickname):
	user = User.query.filter_by(nickname=nickname).first()
	if user is None:
		flash('User %s is not found.' % nickname)
    	return redirect(url_for('index'))
	if user == g.user:
		flash('You can\'t unfollow yourself')
        return redirect(url_for('user', nickname=nickname))
	u = g.user.unfollow(user)
	if u is None:
		flash('Cannot unfollow ' + nickname)
		return redirect(url_for('user', nickname=nickname))
	db.session.add(u)
	db.session.commit()
	flash('You are no longer following ' + nickname)
	return redirect(url_for('user', nickname=nickname)) 


@app.route('/search', methods=['POST'])
@login_required
def search():
	if not g.search_form.validate_on_submit():
		return redirect(url_for('index'))
	return redirect(url_for('search_results', query=g.search_form.search.data))


# sends query into Whoosh
@app.route('/search_results/<query>')
@login_required
def search_results(query):
	results = Post.query.whoosh_search(query, MAX_SEARCH_RESULTS).all()
	return render_template('search_results.html', query=query, results=results)














