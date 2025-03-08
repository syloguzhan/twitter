from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt

db = SQLAlchemy()
bcrypt = Bcrypt()

class User(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    username = db.Column(db.String(80),unique = True,nullable=False)
    password = db.Column(db.String(120),nullable = False)
    posts = db.relationship('Post', backref='author',lazy=True)
    followers = db.relationship('Follow',foreign_keys='Follow.follower_id',backref = 'followed',lazy = 'dynamic')
    following = db.relationship('Follow',foreign_keys='Follow.followed_id',backref='follower', lazy = 'dynamic')

    def set_password(self,password):
        self.password = self.hash_password(password)
    @staticmethod
    def hash_password(password):
        return bcrypt.generate_password_hash(password).decode('utf-8')


class Post(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    content = db.Column(db.String(250),nullable=False)
    user_id = db.Column(db.Integer,db.ForeignKey('user.id'),nullable=False)

class Follow(db.Model):
    id = db.Column(db.Integer,primary_key = True)
    follower_id = db.Column(db.Integer,db.ForeignKey('user.id'),nullable = False)
    followed_id = db.Column(db.Integer,db.ForeignKey('user.id'),nullable = False)

   