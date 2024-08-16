from flask_restful import Resource, reqparse, marshal_with, fields, Api
from flask import Flask, request, jsonify, make_response, abort, render_template, redirect, url_for, flash, session
from model import User, Creator, Playlist, Song, Rate, Album
from flask_sqlalchemy import SQLAlchemy
from werkzeug.exceptions import HTTPException
import json
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy import or_



# ----------- Configurations --------------------------------------------------------#
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.sqlite3'
db = SQLAlchemy()
db.init_app(app)
app.app_context().push()
api = Api(app)
CORS(app)


# Define User model with roles
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement = True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
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
    release_date = db.Column(db.Date, nullable=False)
    genre= db.Column(db.String(100), nullable=False)
    album= db.Column(db.String(100), nullable=False)
    duration = db.Column(db.String, nullable=False)
    lyrics = db.Column(db.String, nullable=False)
    song_file = db.Column(db.String, nullable=False)
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


class NotFoundError(HTTPException):
    def __init__(self, status_code, message=''):
        self.response = make_response(message, status_code)

class NotGivenError(HTTPException):
    def __init__(self, status_code, error_code, error_message):
        message = {"error_code": error_code, "error_message": error_message}
        self.response = make_response(json.dumps(message), status_code)    


user_fields = {
    'id': fields.Integer,
    'username': fields.String,
    'email': fields.String
}

user_parser = reqparse.RequestParser()
user_parser.add_argument('username', type=str, required=True)
user_parser.add_argument('email', type=str, required=True)
user_parser.add_argument('password', type=str, required=True)


song_fields = {
    'id': fields.Integer,
    'title': fields.String,
    'singer': fields.String,
    'release_date': fields.DateTime(dt_format='iso8601'),
    'genre': fields.String,
    'album': fields.String,
    'duration': fields.String,
    'lyrics': fields.String,
    'song_file': fields.String,
    'creator_id': fields.Integer,
    'flag': fields.Boolean,
    'likes': fields.Integer,
    'rating': fields.Float
}  

song_parser = reqparse.RequestParser()
song_parser.add_argument('title', type=str, required=True)
song_parser.add_argument('singer', type=str, required=True)
song_parser.add_argument('release_date', type=str, required=True)
song_parser.add_argument('genre', type=str, required=True)
song_parser.add_argument('album', type=str, required=True)
song_parser.add_argument('duration', type=str, required=True)
song_parser.add_argument('lyrics', type=str, required=True)
song_parser.add_argument('song_file', type=str)
song_parser.add_argument('creator_id', type=int, required=True)
song_parser.add_argument('flag', type=bool)
song_parser.add_argument('likes', type=int)
song_parser.add_argument('rating', type=float)


album_fields = {
    'id': fields.Integer,
    'title': fields.String
}

album_parser = reqparse.RequestParser()
album_parser.add_argument('title', type=str, required=True)
album_parser.add_argument('artist_id', type=int, required=True)


playlist_fields = {
    'id': fields.Integer,
    'title': fields.String
}

playlist_parser = reqparse.RequestParser()
playlist_parser.add_argument('title', type = str, required = True)
playlist_parser.add_argument('user_id', type = int, required = True)




class UserAPI(Resource):

    @marshal_with(user_fields)
    def get(self, user_id):
        user = User.query.filter_by(id=user_id).first()
        if user is None:
            raise NotFoundError(404, 'User not found')
        return user
    
    @marshal_with(user_fields)
    def post(self):
        args = user_parser.parse_args()
        username=args['username']
        email=args['email']
        password=args['password']
        if username is None:
            raise NotGivenError(400, 'USER01', 'Username is not given')
        if email is None:
            raise NotGivenError(400, 'USER02', 'Email is not given')
        if password is None:
            raise NotGivenError(400, 'USER03', 'Password is not given')

        user = User.query.filter_by(username=username).first()
        if user is not None:
            raise NotGivenError(400, 'user_already_exists', 'User already exists')

        user = User(username=username, email=email, password=password)
        db.session.add(user)
        db.session.commit()
        return user

class SongAPI(Resource):

    @marshal_with(song_fields)
    def get(self, song_id):
        song = Song.query.filter_by(id=song_id).first()
        if song is None:
            raise NotFoundError(404, 'Song not found')
        return song

    @marshal_with(song_fields)
    def post(self):
        args = song_parser.parse_args()
        title=args['title']
        singer=args['singer']
        release_date=args['release_date']
        genre=args['genre']
        album=args['album']
        duration=args['duration']
        lyrics=args['lyrics']
        song_file=args['song_file']
        creator_id=args['creator_id']
        flag=args['flag']
        likes=args['likes']
        rating=args['rating']
        if title is None:
            raise NotGivenError(400, 'SONG01', 'Title is not given')
        if singer is None:
            raise NotGivenError(400, 'SONG02', 'Singer is not given')
        if release_date is None:
            raise NotGivenError(400, 'SONG03', 'Release date is not given')
        if genre is None:
            raise NotGivenError(400, 'SONG04', 'Genre is not given')
        if album is None:
            raise NotGivenError(400, 'SONG05', 'Album is not given')
        if duration is None:
            raise NotGivenError(400, 'SONG06', 'Duration is not given')
        if lyrics is None:
            raise NotGivenError(400, 'SONG07', 'Lyrics is not given')
        if creator_id is None:
            raise NotGivenError(400, 'SONG08', 'Creator id is not given')
        if flag is None:
            flag = False
        if likes is None:
            likes = 0
        if rating is None:
            rating = 0
        if song_file is None:
            song_file = ''

        song = Song.query.filter_by(title=title).first()
        if song is not None:
            raise NotGivenError(400, 'SONG09', 'Song already exists')
        date=datetime.strptime(release_date, '%Y-%m-%d')
        album_dup=Album.query.filter_by(title=album).first()
        if album_dup is None:
            album = Album(title=album, artist_id=creator_id)
            db.session.add(album)
            db.session.commit()
        song = Song(title=title, singer=singer, release_date=date, genre=genre, album=album, duration=duration, lyrics=lyrics, song_file=song_file, creator_id=creator_id, flag=flag, likes=likes, rating=rating)
        db.session.add(song)
        db.session.commit()
        return song
    
    @marshal_with(song_fields)
    def put(self,song_id):
        song = Song.query.filter_by(id=song_id).first()
        if song is None:
            raise NotFoundError(404, 'Song not found')
        args = song_parser.parse_args()
        song_dup=Song.query.filter_by(title=args['title']).first()
        if song_dup is not None:
            raise NotGivenError(400, 'SONG09', 'Song already exists')
        song.title=args['title']
        song.singer=args['singer']
        release_date=args['release_date']
        date=datetime.strptime(release_date, '%Y-%m-%d')
        song.release_date=date
        song.genre=args['genre']
        song.album=args['album']
        song.duration=args['duration']
        song.lyrics=args['lyrics']
        song.song_file=args['song_file']
        song.creator_id=args['creator_id']
        song.flag=args['flag']
        song.likes=args['likes']
        song.rating=args['rating']
        db.session.commit()
        return song
    
    def delete(self,song_id):
        song = Song.query.filter_by(id=song_id).first()
        if song is None:
            raise NotFoundError(404, 'Song not found')
        rate=Rate.query.filter_by(song_id=song_id).all()
        for r in rate:
            db.session.delete(r)
        db.session.commit()
        playlist=PlaylistSongs.query.filter_by(song_id=song_id).all()
        for p in playlist:
            db.session.delete(p)
        db.session.commit()
        db.session.delete(song)
        db.session.commit()
        return {'message': 'Song deleted'}
    
class AlbumAPI(Resource):

    @marshal_with(album_fields)
    def get(self, album_id):
        album = Album.query.filter_by(id=album_id).first()
        if album is None:
            raise NotFoundError(404, 'Album not found')
        return album
        
    
    @marshal_with(album_fields)
    def post(self):
        args = album_parser.parse_args()
        title=args['title']
        artist_id=args['artist_id']
        if title is None:
            raise NotGivenError(400, 'ALBUM01', 'Title is not given')
        if artist_id is None:
            raise NotGivenError(400, 'ALBUM02', 'Artist id is not given')

        album = Album.query.filter_by(title=title).first()
        if album is not None:
            raise NotGivenError(400, 'ALBUM03', 'Album already exists')

        album = Album(title=title, artist_id=artist_id)
        db.session.add(album)
        db.session.commit()
        return album
    
    @marshal_with(album_fields)
    def put(self,album_id):
        album = Album.query.filter_by(id=album_id).first()
        if album is None:
            raise NotFoundError(404, 'Album not found')
        args = album_parser.parse_args()
        album_dup=Album.query.filter_by(title=args['title']).first()
        if album_dup is not None:
            raise NotGivenError(400, 'ALBUM03', 'Album already exists')
        album.title=args['title']
        album.artist_id=args['artist_id']
        db.session.commit()
        return album
    
    def delete(self,album_id):
        album = Album.query.filter_by(id=album_id).first()
        if album is None:
            raise NotFoundError(404, 'Album not found')
        song=Song.query.filter_by(album=album.title).all()
        for s in song:
            db.session.delete(s)
        db.session.commit()
        db.session.delete(album)
        db.session.commit()
        return {'message': 'Album deleted'}


class PlaylistAPI(Resource):

    @marshal_with(playlist_fields)
    def get(self, playlist_id):
        playlist = Playlist.query.filter_by(id=playlist_id).first()
        if playlist is None:
            raise NotFoundError(404, 'Playlist not found')
        return playlist
        


    @marshal_with(playlist_fields)
    def post(self):
        args = playlist_parser.parse_args()
        title=args['title']
        user_id=args['user_id']
        if title is None:
            raise NotGivenError(400, 'PLAYLIST01', 'Title is not given')
        if user_id is None:
            raise NotGivenError(400, 'PLAYLIST02', 'User id is not given')

        playlist = Playlist.query.filter_by(title=title).first()
        if playlist is not None:
            raise NotGivenError(400, 'PLAYLIST03', 'Playlist already exists')

        playlist = Playlist(title=title, user_id=user_id)
        db.session.add(playlist)
        db.session.commit()
        return playlist
    
    @marshal_with(playlist_fields)
    def put(self,playlist_id):
        playlist = Playlist.query.filter_by(id=playlist_id).first()
        if playlist is None:
            raise NotFoundError(404, 'Playlist not found')
        args = playlist_parser.parse_args()
        playlist_dup=Playlist.query.filter_by(title=args['title']).first()
        if playlist_dup is not None:
            raise NotGivenError(400, 'PLAYLIST03', 'Playlist already exists')
        playlist.title=args['title']
        playlist.user_id=args['user_id']
        db.session.commit()
        return playlist
    
    def delete(self,playlist_id):
        playlist = Playlist.query.filter_by(id=playlist_id).first()
        if playlist is None:
            raise NotFoundError(404, 'Playlist not found')
        song=PlaylistSongs.query.filter_by(playlist_id=playlist_id).all()
        for s in song:
            db.session.delete(s)
        db.session.commit()
        db.session.delete(playlist)
        db.session.commit()
        return {'message': 'Playlist deleted'}
        


api.add_resource(UserAPI, '/api/users/<int:user_id>', '/api/users')
api.add_resource(SongAPI, '/api/songs/<int:song_id>', '/api/songs')
api.add_resource(AlbumAPI, '/api/album/<int:album_id>', '/api/albums')
api.add_resource(PlaylistAPI, '/api/playlist/<int:playlist_id>', '/api/playlists')

if __name__ == '__main__':
    db.create_all()
    app.run(debug=True,port=8080)