from sqlalchemy import *
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import *
from sqlalchemy.sql import *

engine = create_engine('sqlite:///movies.db')
Base = declarative_base()


##Fact Table
class movie(Base):
    __tablename__='movie'
    movie_id = Column(Integer, primary_key=True)
    movie_name = Column(String)
    release_date = Column(Date)
    release_year = Column(Integer)
    budget = Column(Float)
    revenue = Column(Float)
    profit = Column(Float)
    popularity = Column(Float)

##Dimensions
class genre(Base):
    __tablename__='genre'
    genre_id = Column(Integer, primary_key=True)
    genre = Column(String)

class prod_company(Base):
    __tablename__='production_company'
    prod_company_id = Column(Integer, primary_key=True)
    production_company = Column(String)

##Reference tables
class movie_genre(Base):
    __tablename__='movie_genre'
    mg_id = Column(Integer, primary_key=True)
    movie_id = Column(Integer, ForeignKey('movie.movie_id'))
    genre_id = Column(Integer, ForeignKey('genre.genre_id'))

    movie_r = relationship(movie, backref=backref('movie_genre'))
    genre_r = relationship(genre, backref=backref('movie_genre'))

class movie_prod_company(Base):
    __tablename__='movie_prod_comp'
    mp_id = Column(Integer, primary_key=True)
    movie_id = Column(Integer, ForeignKey('movie.movie_id'))
    prod_company_id = Column(Integer, ForeignKey('production_company.prod_company_id'))

    movie_r = relationship(movie, backref=backref('movie_prod_comp'))
    prod_comp_r = relationship(prod_company, backref=backref('movie_prod_comp'))

def create_database():
    Base.metadata.create_all(engine)