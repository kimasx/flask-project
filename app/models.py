from app import db, app
from hashlib import md5

import sys
if sys.version_info >= (3,0):
	enable_search = False
else:
	enable_search = True
	import flask.ext.whooshalchemy as whooshalchemy


# followers table
followers = db.Table('followers', 
	db.Column('follower_id', db.Integer, db.ForeignKey('user.id')),
	db.Column('followed_id', db.Integer, db.ForeignKey('user.id'))
)


# declare our User class
class User(db.Model):
	# fields are created as instances of db.Column class
	id = db.Column(db.Integer, primary_key=True)
	nickname = db.Column(db.String(64), index=True, unique=True)
	email = db.Column(db.String(120), index=True, unique=True)
	# links a one-to-many relationship to the user's posts
	posts = db.relationship('Post', backref='author', lazy='dynamic')
	about_me = db.Column(db.String(140))
	last_seen = db.Column(db.DateTime)
	followed = db.relationship('User',
								# indicates assoc table used for this relationship
								secondary=followers,
								primaryjoin=(followers.c.follower_id == id),
								secondaryjoin=(followers.c.followed_id == id),
								backref=db.backref('followers', lazy='dynamic'),
								lazy='dynamic')

	# returns true unless the object represents a user that should not be allowed to authenticate
	def is_authenticated(self):
		return True

	# returns true for users unless they are inactive
	def is_active(self):
		return True

	# returns true only for fake users that are not supposed to log in to the system
	def is_anonymous(self):
		return False

	# returns a unique identifier for the user
	def get_id(self):
		try:
			return unicode(self.id)
		except NameError:
			return str(self.id)

	# returns url of the user's avatar img
	def avatar(self, size):
		return 'http://www.gravatar.com/avatar/%s?d=mm&s=%d' % (md5(self.email.encode('utf-8')).hexdigest(), size)

	# user class picks a unique name for us
	@staticmethod
	def make_unique_nickname(nickname):
		if User.query.filter_by(nickname=nickname).first() is None:
			return nickname
		version = 2
		while True:
			new_nickname = nickname + str(version)
			if User.query.filter_by(nickname=new_nickname).first() is None:
				break
			version += 1
		return new_nickname

	def follow(self, user):
		if not self.is_following(user):
			self.followed.append(user)
			return self

	def unfollow(self, user):
		if self.is_following(user):
			self.followed.remove(user)
			return self

	def is_following(self, user):
		return self.followed.filter(followers.c.followed_id == user.id).count() > 0

	def followed_posts(self):
		return Post.query.join(followers, (followers.c.followed_id == Post.user_id)).filter(followers.c.follower_id == self.id).order_by(Post.timestamp.desc())

	def __repr__(self):
		return '<User %r>' % (self.nickname)


# declare our Post class
class Post(db.Model):
	# __searchable__ var is an array with the db fields that will be in the searchable index
	__searchable__ = ['body']

	id = db.Column(db.Integer, primary_key=True)
	body = db.Column(db.String(140))
	timestamp = db.Column(db.DateTime)
	# indicate user_id as foreign key that links to a user
	user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

	def __repr__(self):
		return '<Post %r>' % (self.body)


if enable_search:
	whooshalchemy.whoosh_index(app, Post)







