from app import db
from hashlib import md5

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

	def __repr__(self):
		return '<User %r>' % (self.nickname)


# declare our Post class
class Post(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	body = db.Column(db.String(140))
	timestamp = db.Column(db.DateTime)
	# indicate user_id as foreign key that links to a user
	user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

	def __repr__(self):
		return '<Post %r>' % (self.body)