from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Float
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import requests
import os

API_KEY = os.environ.get('MOVIE_API_KEY') 
SECRET_KEY = os.environ.get('SECRET_KEY') 

app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///top_movies.db'
Bootstrap5(app)

# CREATE DB
class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
db.init_app(app)

# CREATE TABLE
class Movies(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    year: Mapped[str] = mapped_column(Integer)
    description: Mapped[str] = mapped_column(String(250), nullable=False)
    rating: Mapped[float] = mapped_column(Float)
    ranking: Mapped[int] = mapped_column(Integer)
    review: Mapped[str] = mapped_column(String(250), nullable=False)
    img_url: Mapped[str] = mapped_column(String(250), nullable=False)

# CREATE FORM
class EditForm(FlaskForm):
    rating = StringField("Your Rating out of 10 e.g. 7.5", validators=[DataRequired()])
    review = StringField("Your Review", validators=[DataRequired()])
    submit = SubmitField("Done")

class AddForm(FlaskForm):
    title = StringField("Movie Title", validators=[DataRequired()])
    submit = SubmitField("Submit")

with app.app_context():
    db.create_all()

    # new_movie = Movies(
    #    title = 'Phone Booth',
    #    year = 2002,
    #    description = "Publicist Stuart Shepard finds himself trapped in a phone booth, pinned down by an extortionist's sniper rifle. Unable to leave or receive outside help, Stuart's negotiation with the caller leads to a jaw-dropping climax.",
    #    rating = 7.3,
    #    ranking = 10,
    #    review = "My favorite character was the caller.",
    #    img_url = "https://image.tmdb.org/t/p/w500/tjrX2oWRCM3Tvarz38zlZM7Uc10.jpg"
    # )

    # second_movie = Movies(
    #     title="Avatar The Way of Water",
    #     year=2022,
    #     description="Set more than a decade after the events of the first film, learn the story of the Sully family (Jake, Neytiri, and their kids), the trouble that follows them, the lengths they go to keep each other safe, the battles they fight to stay alive, and the tragedies they endure.",
    #     rating=7.3,
    #     ranking=9,
    #     review="I liked the water.",
    #     img_url="https://image.tmdb.org/t/p/w500/t6HIqrRAclMCA60NsSmeqe9RmNV.jpg"
    # )

    # db.session.add(new_movie)
    # db.session.add(second_movie)
    # db.session.commit()

@app.route("/")
def home():
    movies = db.session.execute(db.select(Movies)).scalars()
    return render_template("index.html", movies=movies)

@app.route("/edit/<int:id>", methods=['GET','POST'])
def edit(id):
    form = EditForm()

    if form.validate_on_submit():
        movie = db.session.execute(db.select(Movies).where(Movies.id == id)).scalar()
        movie.rating = form.rating.data
        movie.review = form.review.data
        db.session.commit()

        return redirect(url_for('home'))

    return render_template("edit.html", form=form)

@app.route('/delete/<int:id>')
def delete(id):
    movie = db.session.execute(db.select(Movies).where(Movies.id == id)).scalar()
    db.session.delete(movie)
    db.session.commit()

    return redirect(url_for('home'))

@app.route('/add', methods=['GET','POST'])
def add():
    form = AddForm()

    if form.validate_on_submit():
        title = form.title.data
        url = f"https://api.themoviedb.org/3/search/movie?query={title}&include_adult=false&language=en-US&page=1"
        headers = {'accept': 'application/json'}
        params = {'api_key': API_KEY}
        req = requests.get(url=url, headers=headers, params=params)
        movie_data = req.json()

        return render_template('select.html', movies=movie_data.get('results'))
    
    return render_template('add.html', form=form)

@app.route('/add-movie',methods=['GET','POST'])
def add_movie(id):
        url = f"https://api.themoviedb.org/3/movie/{id}"
        headers = {'accept': 'application/json'}
        params = {'api_key': API_KEY}
        req = requests.get(url=url, headers=headers, params=params)
        movie_data = req.json()

        new_movie = Movies(
            title = movie_data['original_title'],
            year = movie_data['release_date'].split('-')[0],
            description = movie_data['overview'],
            img_url = movie_data['poster_path'],
        )

        db.session.add(new_movie)
        db.session.commit()

        return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(debug=True)
