from flask import Flask, render_template, request, redirect, url_for, flash
from model import db, User, Playlist, Song, Album , Creator, Rate, PlaylistSongs
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
from matplotlib import pyplot as plt
import matplotlib,os


app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///my_music_db.sqlite3"
login_manager = LoginManager(app)
login_manager.login_view = 'login'

db.init_app(app)
app.app_context().push()

# Flask-Login user loader function
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Welcome Page of the App
@app.route("/")
def root():
    return render_template('home.html')

@app.route("/home")
def home():
    return render_template('home.html')

# Routes for login, logout, and home
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    
    # if current_user.is_authenticated:
    #     return redirect(url_for('home'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            creator = Creator.query.filter_by(user_id = user.id).first()
            if creator and creator.listed:
                flash('You are blacklisted and cannot login.','danger')
                return redirect(url_for('login'))
            else:
               # if user and password:
                print('User exists')
                login_user(user)
                return redirect(url_for('userhome'))
        else:
            flash('Login unsuccessful. Please check your username and password.', 'danger')
            return redirect(url_for('login'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))
    # return render_template('home.html')

@app.route('/userhome', methods = ['GET', 'POST'])
@login_required
def userhome():
    if request.method=='GET':
        username=current_user.username
        songs=Song.query.filter_by(flag = False).all()[::-1]
        playlists = Playlist.query.filter_by(user_id = current_user.id).all()
        albums=Album.query.all()
        return render_template('userhome.html', username=username, songs=songs, playlists = playlists, albums=albums)

@app.route('/readlyrics/<id>')
@login_required
def readlyrics(id):
    song=Song.query.filter_by(id=id).first()
    rate=Rate.query.filter_by(song_id=id, user_id=current_user.id).first()
    rates=Rate.query.filter_by(song_id=id).all()
    rates_list=[]
    for i in rates:
        if i.rate:
            r="⭐"*i.rate
            user=User.query.filter_by(id=i.user_id).first().username
            rates_list.append((user,r, i.comment))
    return render_template('read_lyrics.html', song=song,rate=rate,rates=rates_list)

@app.route('/createplaylist', methods=['GET', 'POST'])
@login_required
def createplaylist():
    if request.method=='GET':
        songs = Song.query.filter_by(flag = False).all()
        return render_template('create_playlist.html', id=id, songs = songs)
    if request.method=='POST':
        title=request.form.get('playlist_name')
        songs = request.form.getlist("selected_songs[]")
        print(songs)
        playlist=Playlist.query.filter_by(title=title).first()
        if playlist:
            flash('Playlist already exists!', 'danger')
            return redirect(url_for('createplaylist', id=id))
        if title=='':
            flash('Please enter a valid playlist name!', 'danger')
            return redirect(url_for('createplaylist', id=id))

        new_playlist=Playlist(title=title, user_id=current_user.id)
        db.session.add(new_playlist)
        db.session.commit()
        for i in songs:
            song = Song.query.filter_by(title = i).first()
            new_playlist.songs.append(song)
        db.session.commit()
        flash('Playlist created successfully!', 'success')
        return redirect(url_for('userhome'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        flash('You are already registered and logged in.', 'info')
        return redirect(url_for('userhome'))

    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Check if the username or email already exists
        existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
        if existing_user:
            flash('Username or email already exists. Please choose another.', 'danger')
        else:
            # Create a new user
            hashed_password = generate_password_hash(password)
            new_user = User(username=username, email=email, password=hashed_password, is_creator=False)
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)  # Automatically log in the new user

            return redirect(url_for('userhome'))

    #     error_list = []
    #     if len(password) < 8:
    #         error_list.append('Password must be atleast 8 character long')
        
    #     if not any(i.isdigit() for i in password):
    #         error_list.append('Password must contain atleast 1 digit.')
    
    #     if not any(i.islower() for i in password):
    #         error_list.append('Password must contain atleast 1 lowercase character.')

    #     if not any(i.isupper() for i in password):
    #         error_list.append('Password must contain atleast 1 uppercase character.')

    #     if not any(i in "~!@#$%&*" for i in password):
    #         error_list.append('Password must contain atleast 1 special character.')

    #     error_message = " ".join(error_list)
    #     flash(error_message, 'danger')
    # return render_template('register.html')

@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html', name=current_user.username, email=current_user.email,creator=current_user.is_creator)

@app.route('/creatorregister', methods=['GET', 'POST'])
def creatorregister():
    if request.method=='GET':
        return render_template('creatorregister.html')
    if request.method=='POST':
        genre=request.form.get('genre')
        bio=request.form.get('bio')
        language=request.form.get('language')
        if current_user.is_creator:
            flash('You are already registered as a creator.', 'info')
            return redirect(url_for('creator_page'))
        new_creator=Creator(genre=genre, bio=bio, language=language,user_id=current_user.id)
        db.session.add(new_creator)
        db.session.commit()
        current_user.role='creator'
        current_user.is_creator=True
        db.session.commit()
        return redirect(url_for('creator_page'))

@app.route('/create_album', methods=['GET', 'POST'])
@login_required
def create_album():
    if request.method=='POST':
        title=request.form.get('title')
        if title=='':
            flash('Please enter a valid album name!', 'danger')
            return redirect(url_for('upload_song'))
        album = Album.query.filter_by(title = title).first()
        if album:
            flash("Album already exists!", "danger")
            return redirect(url_for('upload_song'))
        
        new_album=Album(title=title, artist_id=current_user.id)
        db.session.add(new_album)
        db.session.commit()
        flash("Album created successfully!", "success")
        return redirect(url_for('upload_song'))

@app.route('/upload_song', methods=['GET', 'POST'])
@login_required
def upload_song():
    if request.method=='GET':
        albums=Album.query.all()
        return render_template('upload.html', albums=albums)
    if request.method=='POST':
        title=request.form.get('title')
        lyrics=request.form.get('lyrics')
        singer=request.form.get('singer')
        release_date=request.form.get('releaseDate')
        duration=request.form.get('duration')
        album=request.form.get('album')
        genre=request.form.get('genre')
        song_file=request.files.get('song', None)
        if song_file:
            filename = secure_filename(song_file.filename)
            song_file.save('static/songs/' + filename)
        else:
            filename = None
        al=Album.query.filter_by(title=str(album)).first()
        if not al:
            flash('Album does not exists!', 'danger')
            return redirect(url_for('upload_song'))
        date=datetime.strptime(release_date, '%Y-%m-%d')
        new_song=Song(title=title,lyrics=lyrics,creator_id=current_user.id,singer=singer,created_date=date,duration=duration,album=album,genre=genre,song_file=filename)
        db.session.add(new_song)
        db.session.commit()
        return redirect(url_for('creator_page'))

@app.route('/likes/<id>', methods=['GET', 'POST'])
@login_required
def likes(id):
    song=Song.query.filter_by(id=id).first()
    song.likes+=1
    db.session.commit()
    rate=Rate.query.filter_by(song_id=id, user_id=current_user.id).first()
    if rate:
        rate.like=True
        db.session.commit()
    else:
        rate=Rate(song_id=id, user_id=current_user.id,like=True)
        db.session.add(rate)
        db.session.commit()
    return redirect(url_for('readlyrics', id=id))

@app.route('/unlikes/<id>', methods=['GET', 'POST'])
@login_required
def unlikes(id):
    rate=Rate.query.filter_by(song_id=id, user_id=current_user.id).first()
    if rate:
        song=Song.query.filter_by(id=id).first()
        song.likes-=1
        db.session.commit()
        rate.like=False
        db.session.commit()
    return redirect(url_for('readlyrics', id=id))

@app.route('/rate/<id>', methods=['GET', 'POST'])
@login_required
def rate(id):
    song=Song.query.filter_by(id=id).first()
    if request.method=='GET':
        return render_template('rate.html', song=song)
    if request.method=='POST':
        rate=request.form.get('rate')
        comment=request.form.get('comment')
        rates=Rate.query.filter_by(song_id=id, user_id=current_user.id).first()

        if rates:
            rates.rate=rate
            rates.comment=comment
            db.session.commit()
            song.rating=(song.rating+float(rate))/2
            db.session.commit()
        else:
            rates=Rate(song_id=id, user_id=current_user.id,rate=rate,comment=comment)
            db.session.add(rates)
            db.session.commit()
            song.rating=(song.rating+float(rate))/2
            db.session.commit()
        return redirect(url_for('readlyrics', id=id))

# Define the route for the creator page
@app.route('/creator', methods = ['GET', 'POST'])
@login_required
def creator_page():
    if request.method=='GET' and current_user.is_creator:
        Song_list=Song.query.filter_by(creator_id=current_user.id).all()[::-1]
        username=current_user.username
        return render_template('creator.html', username=username, song_list=Song_list)
    if request.method=='GET' and not current_user.is_creator:
        return render_template('non_creator_message.html')

@app.route('/creator_dashboard')
@login_required
def creator_dashboard():
    user_id = current_user.id
    songs = Song.query.filter_by(creator_id = user_id).all()
    Albums=list(set([song.album for song in songs]))
    album_count=len(Albums)
    songs_count=len(songs)
    ratings_list = [float(i.rating) for i in songs]
    if songs:
        avg_rating = sum(ratings_list)/len(ratings_list)
        avg_rating = str(avg_rating)[:4]
    else:
        avg_rating = 0
    return render_template("creator_dashboard.html", songs = songs, album_count=album_count, songs_count=songs_count, avg_rating = avg_rating)

@app.route('/song_delete_confirmation/<id>')
@login_required
def song_delete_confirmation(id):
    if request.method == 'GET':
        return render_template('song_delete_confirmation.html', id = id)
    
@app.route('/song_delete_creator/<id>', methods = ['DELETE', 'GET'])
@login_required
def song_delete_creator(id):
    rate=Rate.query.filter_by(song_id=id).all()
    for r in rate:
        db.session.delete(r)
    db.session.commit()
    playlist=PlaylistSongs.query.filter_by(song_id=id).all()
    for p in playlist:
        db.session.delete(p)
    db.session.commit()
    if Song.query.filter_by(id = id).first().song_file:
        os.remove('static/songs/' + Song.query.filter_by(id = id).first().song_file)
    Songs=Song.query.filter_by(id = id).first()
    db.session.delete(Songs)
    db.session.commit()
    return redirect('/creator_dashboard')

@app.route('/song_delete_confirmation_playlist/<pid>/<id>')
@login_required
def song_delete_confirmation_playlist(pid,id):
    if request.method == 'GET':
        return render_template('song_delete_confirmation_playlist.html', id = id, pid = pid)
    
@app.route('/song_delete_confirmation_album/<aid>/<id>')
@login_required
def song_delete_confirmation_album(aid,id):
    if request.method == 'GET':
        return render_template('song_delete_confirmation_album.html', id = id, aid = aid)
    
@app.route('/song_delete_playlist/<pid>/<id>', methods = ['DELETE', 'GET'])
@login_required
def song_delete_playlist(pid,id):
    playlist_song=PlaylistSongs.query.filter_by(playlist_id = pid, song_id = id).first()
    db.session.delete(playlist_song)
    db.session.commit()
    return redirect(url_for('view_tracks', id = pid)) 

@app.route('/song_delete_album/<aid>/<id>', methods = ['DELETE', 'GET'])
@login_required
def song_delete_album(aid,id):
    album=Album.query.filter_by(id = aid).first()
    Songs=Song.query.filter_by(album = album.title, id = id).first()
    db.session.delete(Songs)
    db.session.commit()
    if len(Song.query.filter_by(album = album.title).all()) == 0:
        db.session.delete(album)
        db.session.commit()
        return redirect('/creator_dashboard')
    return redirect(url_for('view_album_tracks', id = aid))

@app.route('/view_tracks/<id>', methods = ['POST', 'GET'])
@login_required
def view_tracks(id):
    playlist = Playlist.query.filter_by(id = id).first()
    songs = playlist.songs
    song_not_flagged = []
    for song in songs:
        if not song.flag:
            song_not_flagged.append(song)
    return render_template("view_tracks.html", songs = song_not_flagged, name = playlist.title,id = id)

@app.route('/view_album_tracks/<id>', methods = ['POST', 'GET'])
@login_required
def view_album_tracks(id):
    album = Album.query.filter_by(id = id).first()
    songs=Song.query.filter_by(album=album.title).all()
    song_not_flagged = []
    for song in songs:
        if not song.flag:
            song_not_flagged.append(song)
    return render_template("view_album_tracks.html", songs = song_not_flagged, name = album.title, id = id, creator=current_user.is_creator)

@app.route('/edit_songs/<id>', methods=['POST', 'GET'])
@login_required
def edit_songs(id):
    Songs = Song.query.filter_by(id=id).first()
    if request.method == "GET":
        albums = Album.query.all()
        return render_template("edit_songs.html", Songs=Songs, albums=albums)

    if request.method == "POST":
        Songs.title = request.form.get("title")
        Songs.singer = request.form.get("singer")
        Songs.releaseDate = request.form.get("releaseDate")
        Songs.genre = request.form.get("genre")
        Songs.album = request.form.get("album")
        Songs.duration = request.form.get("duration")
        Songs.lyrics = request.form.get("lyrics")

        # Corrected line to get the file from the request
        song_file = request.files.get("song")

        # Check if a file was provided
        if song_file:
            filename = secure_filename(song_file.filename)
            song_file.save('static/songs/' + filename)
            Songs.song_file =filename
        else:
            flash("No file uploaded", "danger")

        db.session.commit()
        return redirect("/creator_dashboard")

# Define a route for non-creators (you can customize this route based on your needs)
@app.route('/non-creator-message')
def non_creator_message():
    return render_template('non_creator_message.html')

# Define the route for admin login
@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'GET':
        return render_template('admin_login.html')
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password,password) and user.role=='admin':
            login_user(user)
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Login unsuccessful. Please check your username and password.', 'danger')
            return redirect(url_for('admin_login'))

# Define the route for the admin dashboard
@app.route('/admin_dashboard')
@login_required
def admin_dashboard():
    # Check if the current user is an admin
    if current_user.role=='admin':
        # Render the admin dashboard template
        users=User.query.all()
        normal_users=[ user for user in users if user.role=='normal']
        creators=[ user for user in users if user.role=='creator']
        normal_users_count=len(normal_users)
        creators_count=len(creators)
        Songs=Song.query.all()
        Albums=Album.query.all()
        genre=[song.genre for song in Songs]
        genre=list(set(genre))
        genre_count=len(genre)
        album_count=len(Albums)
        songs_count=len(Songs)
        top_5_songs=Song.query.order_by(Song.likes.desc()).limit(5).all()
        d={}
        for song in top_5_songs:
            d[song.title]=song.likes
        x_values=list(d.keys())
        y_values=list(d.values())
        matplotlib.use('Agg')
        plt.figure(figsize=(6,5))
        plt.clf()
        plt.bar(x_values, y_values, color='b')
        plt.xticks(rotation=45, ha="right")
        plt.xlabel('Song Title')
        plt.ylabel('Likes')
        plt.title('Popular songs')
        plt.tight_layout()
        plt.savefig("static/popular_songs.png")
        genre={}
        for song in Songs:
            if song.genre in genre:
                genre[song.genre]+=song.likes
            else:
                genre[song.genre]=song.likes
        top_5_genre=dict(sorted(genre.items(), key=lambda item: item[1], reverse=True)[:5])
        x_values=list(top_5_genre.keys())
        y_values=list(top_5_genre.values())
        matplotlib.use('Agg')
        plt.figure(figsize=(6, 5))
        plt.clf()
        plt.bar(x_values, y_values, color='b')
        plt.xticks(rotation=45, ha="right")
        plt.xlabel('Genre')
        plt.ylabel('Likes')
        plt.title('Popular genres')
        plt.tight_layout()
        plt.savefig("static/popular_genres.png")
        creators=Creator.query.all()
        creator_songs={}
        for creator in creators:
            creator_songs[creator.user.username]=len(Song.query.filter_by(creator_id=creator.user_id).all())
        top_5_creators=dict(sorted(creator_songs.items(), key=lambda item: item[1], reverse=True)[:5])
        x_values=list(top_5_creators.keys())
        y_values=list(top_5_creators.values())
        matplotlib.use('Agg')
        plt.figure(figsize=(6, 5))
        plt.clf()
        plt.bar(x_values, y_values, color='b')
        plt.xticks(rotation=45, ha="right")
        plt.xlabel('Creator')
        plt.ylabel('Number of songs')
        plt.title('Top creators')
        plt.tight_layout()
        plt.savefig("static/popular_creators.png")
        return render_template('admin_dashboard.html', name=current_user.username, normal_users_count=normal_users_count, creators_count=creators_count, genre_count=genre_count, album_count=album_count, songs_count=songs_count)
    else:
        flash('You do not have permission to access the admin dashboard.', 'danger')
        return redirect(url_for('home'))  # Redirect to the home page or another appropriate route

@app.route('/tracks')
@login_required
def tracks():
    Songs=Song.query.all()
    tracks={}
    for song in Songs:
        if song.genre in tracks:
            tracks[song.genre].append(song)
        else:
            tracks[song.genre]=[song]
    return render_template('tracks.html', tracks=tracks)

@app.route('/song_delete_confirm/<id>')
@login_required
def song_delete_confirm(id):
    if request.method == 'GET':
        return render_template('song_delete_confirm.html', id = id)

@app.route('/delete_playlist_confirmation/<id>')
@login_required
def delete_playlist_confirmation(id):
    if request.method == 'GET':
        return render_template('delete_playlist_confirmation.html', id = id)
    
@app.route('/delete_playlist/<id>')
@login_required
def delete_playlist(id):
    playlist = Playlist.query.filter_by(id = id).first()
    playlist_songs = PlaylistSongs.query.filter_by(playlist_id = id).all()
    for song in playlist_songs:
        db.session.delete(song)
    db.session.commit()
    db.session.delete(playlist)
    db.session.commit()
    return redirect('/userhome')


@app.route('/song_delete_admin/<id>', methods = ['DELETE', 'GET'])
@login_required
def song_delete_admin(id):
    rate=Rate.query.filter_by(song_id=id).all()
    for r in rate:
        db.session.delete(r)
    db.session.commit()
    playlist=PlaylistSongs.query.filter_by(song_id=id).all()
    for p in playlist:
        db.session.delete(p)
    db.session.commit()
    if Song.query.filter_by(id = id).first().song_file:
        os.remove('static/songs/' + Song.query.filter_by(id = id).first().song_file)
    Songs=Song.query.filter_by(id = id).first()
    db.session.delete(Songs)
    db.session.commit()
    return redirect('/tracks')

@app.route('/song_flag/<id>', methods = ['DELETE', 'GET'])
@login_required
def song_flag(id):
    Songs =Song.query.filter_by(id = id).first()
    Songs.flag = True
    db.session.commit()
    flash('Song flagged successfully!', 'success')
    return redirect('/tracks')

@app.route('/song_unflag/<id>', methods = ['DELETE', 'GET'])
@login_required
def song_unflag(id):
    Songs =Song.query.filter_by(id = id).first()
    Songs.flag = False
    db.session.commit()
    flash('Song unflagged successfully!', 'success')
    return redirect('/tracks')


@app.route('/addsong/<id>', methods = ['POST', 'GET'])
@login_required
def addsong(id):
    if request.method == 'GET':
        songs=Song.query.filter_by(flag = False).all()
        playlist = Playlist.query.filter_by(id = id).first()
        return render_template('add_song.html', id = id, songs = songs,playlist=playlist)
    if request.method == 'POST':
        songs = request.form.getlist("selected_songs[]")
        playlist = Playlist.query.filter_by(id = id).first()
        for i in songs:
            song = Song.query.filter_by(title = i).first()
            playlist.songs.append(song)
        db.session.commit()
        return redirect(url_for('view_tracks', id = id))


@app.route('/search', methods = ['POST', 'GET'])
@login_required
def search():
    search = request.form.get("search")
    songs = Song.query.filter(Song.genre.ilike("%"+search+"%")).all()
    songs += Song.query.filter(Song.title.ilike("%"+search+"%")).all()
    if songs:
        albums={}
        for song in songs:
            if not song.flag:
                if song.album in albums:
                    albums[song.album].append(song)
                else:
                    albums[song.album]=[song]
            else:
                flash("Sorry! No results found", "danger")
                return redirect("/userhome")
        return render_template("search.html", albums = albums)
    singers = Song.query.filter(Song.singer.ilike("%"+search+"%")).first()
    if singers:
        songs = Song.query.filter_by(singer = singers.singer).all()
        albums={}
        for song in songs:
            if not song.flag:
                if song.album in albums:
                    albums[song.album].append(song)
                else:
                    albums[song.album]=[song]
            else:
                flash("Sorry! No results found", "danger")
                return redirect("/userhome")
        return render_template("search.html", albums = albums)
    genre=Song.query.filter(Song.genre.ilike("%"+search+"%")).first()
    if genre:
        songs = Song.query.filter_by(genre = genre.genre).all()
        albums={}
        for song in songs:
            if not song.flag:
                if song.album in albums:
                    albums[song.album].append(song)
                else:
                    albums[song.album]=[song]
            else:
                flash("Sorry! No results found", "danger")
                return redirect("/userhome")
        return render_template("search.html", albums = albums)
        genre=Song.query.filter(Song.genre.ilike("%"+search+"%")).first()
    album=Song.query.filter(Song.album.ilike("%"+search+"%")).first()
    if album:
        songs = Song.query.filter_by(album = album.album).all()
        albums={}
        for song in songs:
            if not song.flag:
                if song.album in albums:
                    albums[song.album].append(song)
                else:
                    albums[song.album]=[song]
            else:
                flash("Sorry! No results found", "danger")
                return redirect("/userhome")
        return render_template("search.html", albums = albums)
    else:
        flash("Sorry! No results found", "danger")
        return redirect("/userhome")
    
@app.route('/admin_creators', methods = ['POST', 'GET'])
def creators():
    if request.method == 'GET':
        user=User.query.all()
        creators=[]
        for i in user:
            if i.is_creator:
                creator=Creator.query.filter_by(user_id=i.id).first()
                creators.append((i,creator.listed))
        return render_template('admin_creators.html', creators = creators)
    
@app.route('/creator_whitelist/<id>')
def creator_whitelist(id):
    creator=Creator.query.filter_by(user_id=id).first()
    creator.listed=False
    song=Song.query.filter_by(creator_id=id).all()
    for i in song:
        i.flag=False
    db.session.commit()
    flash('Creator whitelisted successfully!', 'success')
    return redirect('/admin_creators')

@app.route('/creator_blacklist/<id>')
def creator_blacklist(id):
    creator=Creator.query.filter_by(user_id=id).first()
    creator.listed=True
    song=Song.query.filter_by(creator_id=id).all()
    for i in song:
        i.flag=True
    db.session.commit()
    flash('Creator blacklisted successfully!', 'success')
    return redirect('/admin_creators')

@app.route('/ratesearch/<rate>')
@login_required
def ratesearch(rate):
    Songs=Song.query.all()
    songs=[]
    for song in Songs:
        if song.rating>4 and song.rating<=5 and rate=='5':
            songs.append(song)
        elif song.rating>3 and song.rating<=4 and rate=='4':
            songs.append(song)
        elif song.rating>2 and song.rating<=3 and rate=='3':
            songs.append(song)
        elif song.rating>1 and song.rating<=2 and rate=='2':
            songs.append(song)
        elif song.rating>=0 and song.rating<=1 and rate=='1':
            songs.append(song)
    albums={}
    for song in songs:
        if song.album in albums:
            albums[song.album].append(song)
        else:
            albums[song.album]=[song]
    return render_template('search.html', albums=albums)


if __name__ == '__main__':
    db.create_all()
    app.run(debug =True)