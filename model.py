from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import datetime

db = SQLAlchemy()

# Define User model with roles
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True, autoincrement = True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=True)
    role = db.Column(db.String(20), default='normal')  # Roles: normal, creator, admin
    is_creator = db.Column(db.Boolean, default=False)

    playlists = db.relationship('Playlist', backref='owner', lazy=True)
    songs = db.relationship('Song', backref='artist', lazy=True)

class Creator(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement = True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    bio= db.Column(db.String(1000), nullable=False)
    genre= db.Column(db.String(100), nullable=False)
    language= db.Column(db.String(100), nullable=False)
    listed= db.Column(db.Boolean, nullable=False, default=False)
    user= db.relationship('User', backref='creator', lazy=True)

# Define Playlist model
class Playlist(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement = True)
    title = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    songs = db.relationship('Song', secondary='playlist_songs', backref='playlist', lazy=True)

# Define Song model
class Song(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement = True)
    title = db.Column(db.String(100), nullable=False)
    singer = db.Column(db.String(100), nullable=False)
    created_date = db.Column(db.DateTime(), default=datetime.now(), nullable=False)
    genre= db.Column(db.String(100), nullable=False)
    album= db.Column(db.String(100), nullable=False)
    duration = db.Column(db.String, nullable=False)
    lyrics = db.Column(db.String, nullable=False)
    song_file = db.Column(db.String, nullable=True)
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    flag = db.Column(db.Boolean, nullable = False, default = False)
    likes = db.Column(db.Integer, nullable = False, default = 0)
    rating = db.Column(db.Float, nullable = False, default = 0)
    
class Rate(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement = True)
    song_id = db.Column(db.Integer, db.ForeignKey('song.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    rate = db.Column(db.Integer, nullable=True, default=0)
    like= db.Column(db.Boolean, nullable=True)
    comment= db.Column(db.String(1000), nullable=True)
    user= db.relationship('User', backref='rate', lazy=True)


# Define Album model
class Album(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement = True)
    title = db.Column(db.String(100), nullable=False)
    artist_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

# Define association table for playlist and songs
class PlaylistSongs(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement = True)
    playlist_id = db.Column(db.Integer, db.ForeignKey('playlist.id'), nullable=False)
    song_id = db.Column(db.Integer, db.ForeignKey('song.id'), nullable=False)

