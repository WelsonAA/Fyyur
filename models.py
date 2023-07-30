from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

from app import format_datetime,app
db = SQLAlchemy(app)
migrate = Migrate(app, db)

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
    shows = db.relationship('Show', backref="venue", lazy=True)
    website = db.Column(db.String(500), nullable=True)
    seeking_talent = db.Column(db.Boolean, default=False, nullable=False)
    seeking_description = db.Column(db.String(100), nullable=True)
    genres = db.relationship('Venue_Genres', backref="venue_genres", lazy=True)

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
    shows = db.relationship("Show", backref="artist", lazy=True)
    genres = db.relationship('Artist_Genres', backref="artist_genres", lazy=True)

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
    show_id = db.Column(db.Integer, primary_key=True)
    artist_id = db.Column(db.Integer, db.ForeignKey('artists.id'), primary_key=False)
    venue_id = db.Column(db.Integer, db.ForeignKey('venues.id'), primary_key=False)
    start_time = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f"<Show {self.show_id}, {self.venue_id}, {self.artist_id}, {format_datetime(value=self.start_time)}>"

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
