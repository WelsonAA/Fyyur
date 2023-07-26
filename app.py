# ----------------------------------------------------------------------------#
# Imports
# ----------------------------------------------------------------------------#

import json
import sys

import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for, jsonify, abort
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from sqlalchemy.orm import Query

import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate

# ----------------------------------------------------------------------------#
# App Config.
# ---------------------------------------------------------------------------
app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# ----------------------------------------------------------------------------#
# Models.
# ----------------------------------------------------------------------------#


class Venue(db.Model):
    __tablename__ = 'venues'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    shows = db.relationship('Show', backref="venue", lazy=False)
    website = db.Column(db.String(500), nullable=True)
    seeking_talent = db.Column(db.Boolean, default=False, nullable=False)
    seeking_description = db.Column(db.String(100), nullable=True)
    genres = db.relationship('Venue_Genres', backref="venue_genres", lazy=False)

    def dictforvenues(self):
        c = len(Show.query.filter_by(venue_id=self.id).all())
        return {"id": self.id,
                "name": self.name,
                "num_upcoming_shows": c
                }

    def __repr__(self):
        return f"<Venue {self.id}, {self.name}, {self.city}, {self.state}>\n"

    def __str__(self):
        return f"<Venue {self.id}, {self.name}, {self.city}>"


class Venue_Genres(db.Model):
    __tablename__ = 'venue_genres'
    venue_id = db.Column(db.Integer, db.ForeignKey('venues.id'), primary_key=True)
    genre = db.Column(db.String(100), primary_key=True)

    def __repr__(self):
        return f"<Venue_Genres {self.venue_id}, {self.genre}>"


class Artist(db.Model):
    __tablename__ = 'artists'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(500), nullable=True)
    seeking_venue = db.Column(db.Boolean, default=False, nullable=False)
    seeking_description = db.Column(db.String(100), nullable=True)
    shows = db.relationship("Show", backref="artist", lazy=False)
    genres = db.relationship('Artist_Genres', backref="artist_genres", lazy=False)

    def dictforartists(self):
        return {
            "id": self.id,
            "name": self.name
        }

    def dictforsearchartists(self):
        artist_shows = Show.query.filter_by(artist_id=self.id).all()
        count = 0
        for artist_show in artist_shows:
            if artist_show.start_time is None or artist_show.start_time >= datetime.now():
                count += 1
        return {
            "id": self.id,
            "name": self.name,
            "num_upcoming_shows": count
        }

    def __repr__(self):
        return f"<Artist {self.id}, {self.name}>"



class Artist_Genres(db.Model):
    __tablename__ = 'artist_genres'
    artist_id = db.Column(db.Integer, db.ForeignKey('artists.id'), primary_key=True)
    genre = db.Column(db.String(100), primary_key=True)

    def __repr__(self):
        return f"<Artist_Genres {self.artist_id}, {self.genre}>"


class Show(db.Model):
    __tablename__ = "shows"
    artist_id = db.Column(db.Integer, db.ForeignKey('artists.id'), primary_key=True)
    venue_id = db.Column(db.Integer, db.ForeignKey('venues.id'), primary_key=True)
    start_time = db.Column(db.DateTime, nullable=True)

    def dictforshows(self):
        return {
            "venue_id": self.venue_id,
            "venue_name": Venue.query.get(self.venue_id),
            "artist_id": self.artist_id,
            "artist_name": Artist.query.get(self.artist_id).name,
            "artist_image_link": Artist.query.get(self.artist_id).image_link,
            "start_time": format_datetime(self.start_time)
        }

    def dictforvenues(self):
        return {
            "artist_id": self.artist_id,
            "artist_name": Artist.query.get(self.artist_id).name,
            "artist_image_link": Artist.query.get(self.artist_id).image_link,
            "start_time": format_datetime(self.start_time)
        }

    def dictforartists(self):
        return {
            "venue_id": self.venue_id,
            "venue_name": Venue.query.get(self.venue_id).name,
            "venue_image_link": Venue.query.get(self.venue_id).image_link,
            "start_time": self.start_time
        }

    def __repr__(self):
        return f"<Show {self.venue_id}, {self.artist_id}, {format_datetime(value=self.start_time)}>"



# ----------------------------------------------------------------------------#
# Filters.
# ----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
    if value is None or value == "":
        return ""
    date = dateutil.parser.parse(value)
    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format, locale='en')


app.jinja_env.filters['datetime'] = format_datetime


# ----------------------------------------------------------------------------#
# Controllers.
# ----------------------------------------------------------------------------#

@app.route('/')
def index():
    return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
    areas = Venue.query.with_entities(func.count(Venue.id),
                                      Venue.city,
                                      Venue.state
                                      ).group_by(Venue.city, Venue.state).all()
    data = []
    for area in areas:
        area_venues = Venue.query.filter_by(state=area.state).filter_by(city=area.city).all()
        venue_data = []
        for venue in area_venues:
            venue_data.append(venue.dictforvenues())
        data.append({
            "city": area.city,
            "state": area.state,
            "venues": venue_data
        })
    return render_template('pages/venues.html', areas=data);


@app.route('/venues/search', methods=['GET'])
def search_venues():

    search_term = request.args.get('search_term')
    res = Venue.query.filter(Venue.name.like(f'%{search_term}%')).all()
    data = []
    for venue in res:
        data.append(venue.dictforvenues())
    response = {
        "count": len(data),
        "data": data
    }
    return render_template('pages/search_venues.html', results=response,
                           search_term=search_term)


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    # shows the venue page with the given venue_id
    # TODO: replace with real venue data from the venues table, using venue_id
    shows_list = Show.query.filter_by(venue_id=venue_id).all()
    artists_ids = []
    past_shows = []
    upcoming_shows = []
    for show in shows_list:
        artists_ids.append(show.artist_id)
        if show.start_time is None:
            upcoming_shows.append(show.dictforvenues())
        elif show.start_time < datetime.now():
            past_shows.append(show.dictforvenues())
        else:
            upcoming_shows.append(show.dictforvenues())
    this_venue = Venue.query.get(venue_id)
    genres_list = []
    genres = Venue_Genres.query.with_entities(Venue_Genres.genre).filter_by(venue_id=venue_id).all()
    for genre in genres:
        genres_list.append(genre.genre)
    data = {
        "id": venue_id,
        "name": this_venue.name,
        "genres": genres_list,
        "address": this_venue.address,
        "city": this_venue.city,
        "state": this_venue.state,
        "phone": this_venue.phone,
        "website": this_venue.website,
        "facebook_link": this_venue.facebook_link,
        "seeking_talent": this_venue.seeking_talent,
        "seeking_description": this_venue.seeking_description,
        "image_link": this_venue.image_link,
        "past_shows": past_shows,
        "upcoming_shows": upcoming_shows,
        "past_shows_count": len(past_shows),
        "upcoming_shows_count": len(upcoming_shows),
    }
    return render_template('pages/show_venue.html', venue=data)


#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    error = False
    try:
        name = request.form.get('name', '')
        city = request.form.get('city', '')
        state = request.form.get('state', '')
        address = request.form.get('address')
        phone = request.form.get('phone', '')
        genres = request.form.getlist('genres')
        facebook_link = request.form.get('facebook_link', '')
        image_link = request.form.get('image_link', '')
        website = request.form.get('website_link', '')
        seeking_description = request.form.get('seeking_description', '')
        seeking_talent = request.form.get('seeking_talent', 'n')
        if seeking_talent != 'y':
            seeking_talent = False
            seeking_description = ""
        else:
            seeking_talent = True
        v = Venue(name=name, city=city, state=state, address=address, phone=phone, facebook_link=facebook_link,
                  image_link=image_link, website=website, seeking_talent=seeking_talent,
                  seeking_description=seeking_description)
        db.session.add(v)
        db.session.commit()
        for genre in genres:
            vg = Venue_Genres(venue_id=v.id, genre=genre)
            db.session.add(vg)
            db.session.commit()
    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close
    if error:
        flash('Venue ' + request.form['name'] + ' was not listed due to an error!')
    else:
        flash('Venue ' + request.form['name'] + ' was successfully listed!')
        return render_template('pages/home.html')


@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
    error = False
    try:
        this_venue = Venue.query.get(venue_id)
        db.session.delete(this_venue)
        db.session.commit()
    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close
    if error:
        abort(500)
    else:
        return render_template('pages/home.html')


#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
    # TODO: replace with real data returned from querying the database
    arts = Artist.query.all()
    data = []
    for artist in arts:
        data.append(artist.dictforartists())
    return render_template('pages/artists.html', artists=data)


@app.route('/artists/search', methods=['POST'])
def search_artists():
    # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
    # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
    # search for "band" should return "The Wild Sax Band".
    search_term = request.form.get('search_term', '')
    res = Artist.query.filter(Artist.name.like(f'%{search_term}%')).all()
    data = []
    for artist in res:
        data.append(artist.dictforsearchartists())
    response = {
        "count": len(data),
        "data": data
    }

    return render_template('pages/search_artists.html', results=response,
                           search_term=search_term)


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    # shows the artist page with the given artist_id
    # TODO: replace with real artist data from the artist table, using artist_id
    this_artist = Artist.query.get(artist_id)
    artist_shows = Show.query.filter_by(artist_id=artist_id).all()
    past_shows = []
    upcoming_shows = []
    for artist_show in artist_shows:
        if artist_show.start_time is None or artist_show.start_time >= datetime.now():
            upcoming_shows.append(artist_show.dictforartists())
        else:
            past_shows.append(artist_show.dictforartists())
    genres_list = []
    genres = Artist_Genres.query.with_entities(Artist_Genres.genre).filter_by(artist_id=artist_id).all()
    for genre in genres:
        genres_list.append(genre.genre)
    data = {
        "id": this_artist.id,
        "name": this_artist.name,
        "genres": genres_list,
        "city": this_artist.city,
        "state": this_artist.state,
        "phone": this_artist.phone,
        "website": this_artist.website,
        "facebook_link": this_artist.facebook_link,
        "seeking_venue": this_artist.seeking_venue,
        "seeking_description": this_artist.seeking_description,
        "image_link": this_artist.image_link,
        "past_shows": past_shows,
        "upcoming_shows": upcoming_shows,
        "past_shows_count": len(past_shows),
        "upcoming_shows_count": len(upcoming_shows),
    }
    return render_template('pages/show_artist.html', artist=data)


#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    this_artist = Artist.query.get(artist_id)
    if this_artist:
        genres_list = []
        genres = Artist_Genres.query.with_entities(Artist_Genres.genre).filter_by(artist_id=artist_id).all()
        for genre in genres:
            genres_list.append(genre.genre)

        form = ArtistForm()
        form.name.data = this_artist.name
        form.city.data = this_artist.city
        form.state.data = this_artist.state
        form.phone.data = this_artist.phone
        form.website_link.data = this_artist.website
        form.image_link.data = this_artist.image_link
        form.seeking_description.data = this_artist.seeking_description
        form.facebook_link.data = this_artist.facebook_link
        form.genres.data = genres_list
        form.seeking_venue.data = this_artist.seeking_venue
    else:
        abort(404)
    return render_template('forms/edit_artist.html', form=form, artist=this_artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    this_artist = Artist.query.get(artist_id)
    old_genres = Artist_Genres.query.with_entities(Artist_Genres.genre).filter_by(artist_id=artist_id).all()
    old_genres_list = []
    for old_genre in old_genres:
        old_genres_list.append(old_genre.genre)
    error = False
    try:
        new_genres = request.form.getlist('genres')
        this_artist.name = request.form.get('name', '')
        this_artist.city = request.form.get('city', '')
        this_artist.state = request.form.get('state', '')
        this_artist.phone = request.form.get('phone', '')
        this_artist.facebook_link = request.form.get('facebook_link', '')
        this_artist.image_link = request.form.get('image_link', '')
        this_artist.website = request.form.get('website_link', '')
        this_artist.seeking_description = request.form.get('seeking_description', '')
        this_artist.seeking_venue = request.form.get('seeking_venue', 'n')
        if this_artist.seeking_venue != 'y':
            this_artist.seeking_venue = False
            this_artist.seeking_description = ""
        else:
            this_artist.seeking_venue = True

        db.session.add(this_artist)
        db.session.commit()
        for new_genre in new_genres:
            ag = Artist_Genres.query.filter_by(artist_id=artist_id).filter_by(genre=new_genre).first()
            if ag is None:
                ag = Artist_Genres(artist_id=artist_id, genre=new_genre)
                db.session.add(ag)
                db.session.commit()
        for old_genre in old_genres_list:
            if old_genre not in new_genres:
                agd = Artist_Genres.query.filter_by(artist_id=artist_id).filter_by(genre=old_genre).first()
                db.session.delete(agd)
                db.session.commit()
    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close

    return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    this_venue = Venue.query.get(venue_id)
    if this_venue:
        genres_list = []
        genres = Venue_Genres.query.with_entities(Venue_Genres.genre).filter_by(venue_id=venue_id).all()
        for genre in genres:
            genres_list.append(genre.genre)
        form = VenueForm()
        form.genres.data = genres_list
        form.seeking_talent.data = this_venue.seeking_talent
        form.name.data = this_venue.name
        form.city.data = this_venue.city
        form.state.data = this_venue.state
        form.phone.data = this_venue.phone
        form.address.data = this_venue.address
        form.website_link.data = this_venue.website
        form.image_link.data = this_venue.image_link
        form.seeking_description.data = this_venue.seeking_description
        form.facebook_link.data = this_venue.facebook_link
        form.genres.data = genres_list
        return render_template('forms/edit_venue.html', form=form, venue=this_venue)
    else:
        abort(404)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    this_venue = Venue.query.get(venue_id)
    old_genres = Venue_Genres.query.with_entities(Venue_Genres.genre).filter_by(venue_id=venue_id).all()
    old_genres_list = []
    for old_genre in old_genres:
        old_genres_list.append(old_genre.genre)
    error = False
    try:
        new_genres = request.form.getlist('genres')
        this_venue.name = request.form.get('name', '')
        this_venue.city = request.form.get('city', '')
        this_venue.state = request.form.get('state', '')
        this_venue.address = request.form.get('address')
        this_venue.phone = request.form.get('phone', '')
        this_venue.facebook_link = request.form.get('facebook_link', '')
        this_venue.image_link = request.form.get('image_link', '')
        this_venue.website = request.form.get('website_link', '')
        this_venue.seeking_description = request.form.get('seeking_description', '')
        this_venue.seeking_talent = request.form.get('seeking_talent', 'n')
        if this_venue.seeking_talent != 'y':
            this_venue.seeking_talent = False
            this_venue.seeking_description = ""
        else:
            this_venue.seeking_talent = True

        db.session.add(this_venue)
        db.session.commit()
        for genre in new_genres:
            vg = Venue_Genres.query.filter_by(venue_id=venue_id).filter_by(genre=genre).first()
            if vg is None:
                vg = Venue_Genres(venue_id=venue_id, genre=genre)
                db.session.add(vg)
                db.session.commit()
        for old_genre in old_genres_list:
            if old_genre not in new_genres:
                vgd = Venue_Genres.query.filter_by(venue_id=venue_id).filter_by(genre=old_genre).first()
                db.session.delete(vgd)
                db.session.commit()
    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close
    if error:
        abort(500)
    else:
        return redirect(url_for('show_venue', venue_id=venue_id))



#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    error = False
    try:
        name = request.form.get('name', '')
        city = request.form.get('city', '')
        state = request.form.get('state', '')
        phone = request.form.get('phone', '')
        genres = request.form.getlist('genres')
        facebook_link = request.form.get('facebook_link', '')
        image_link = request.form.get('image_link', '')
        website = request.form.get('website_link', '')
        seeking_description = request.form.get('seeking_description', '')
        seeking_venue = request.form.get('seeking_venue', 'n')
        # on successful db insert, flash success
        if seeking_venue != 'y':
            seeking_venue = False
            seeking_description = ""
        else:
            seeking_venue = True
        a = Artist(name=name, city=city, state=state, phone=phone, facebook_link=facebook_link,
                   image_link=image_link, website=website, seeking_venue=seeking_venue,
                   seeking_description=seeking_description)
        db.session.add(a)
        db.session.commit()
        for genre in genres:
            ag = Artist_Genres(artist_id=a.id, genre=genre)
            db.session.add(ag)
            db.session.commit()
    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close
    if error:
        flash('Artist ' + request.form['name'] + ' was not listed due to an error!')
    else:
        flash('Artist ' + request.form['name'] + ' was successfully listed!')
        return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
    # displays list of shows at /shows
    # TODO: replace with real venues data.
    shows_list = Show.query.all()
    data = []
    for show in shows_list:
        data.append(show.dictforshows())
    return render_template('pages/shows.html', shows=data)


@app.route('/shows/create')
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    # called to create new shows in the db, upon submitting new show listing form
    # TODO: insert form data as a new Show record in the db, instead
    error = False
    try:
        artist_id = request.form.get('artist_id', '')
        venue_id = request.form.get('venue_id', '')
        start_time = request.form.get('start_time', '')
        s = Show(artist_id=artist_id, venue_id=venue_id, start_time=start_time)
        db.session.add(s)
        db.session.commit()
    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close
    if error:
        flash('Show was not listed due to an error!')
    else:
        flash('Show was successfully listed!')
        return render_template('pages/home.html')


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

# ----------------------------------------------------------------------------#
# Launch.
# ----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
