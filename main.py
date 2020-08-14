##So the idea here is to import into a sqlite Database simulating
#possibly a Redshift database and this would definitely be a lambda
#But to scale I would probably use S3 and query it from Redshift


import pandas as pd
import json
from db import *
from sqlalchemy import *
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import *
from sqlalchemy.sql import *
import datetime
import ast

def import_data(csv_file):
    df = pd.read_csv(csv_file,
                        quotechar='"',
                        low_memory=False)

    ##clean data and create profit field
    df = df[['title', 'release_date','genres', 'production_companies' ,'popularity', 'revenue' ,'budget']]
    #Because of the messy parts of the data I will coerece the fields that are showing the wrong data
    #The idea is that I would need to ask the source owner why these fields are messy
    df['budget'] = pd.to_numeric(df['budget'], errors='coerce')
    df['popularity'] = pd.to_numeric(df['popularity'], errors='coerce')
    df['release_date'] = pd.to_datetime(df['release_date'], errors='coerce')
    df = df.astype({'genres':'string', 'production_companies': 'string'})

    df['profit'] = df['revenue'] - df['budget']
    df['release_year'] = pd.DatetimeIndex(df['release_date']).year
    
    #set nulls to a null date
    df['release_date']=df['release_date'].fillna(datetime.date(1900,1,1))
    df['release_year']=df['release_year'].fillna(1900)
    
    return df


##run
create_database()

df = import_data('./the-movies-dataset/movies_metadata.csv')
record_insert_count = 0
session = sessionmaker(bind=engine)()
for index, row in df.iterrows():
    try:
        #Check for if movie already exists in database
        if session.query(movie).filter(movie.movie_name==row['title']).count() == 0:
            temp_mov = movie(movie_name=row['title'],
                            release_date=row['release_date'],
                            release_year=row['release_year'],
                            budget=row['budget'],
                            revenue=row['revenue'],
                            profit=row['profit'],
                            popularity=row['popularity'])
            session.add(temp_mov)
            
            #Add Genres to genre table
            for genre_i in ast.literal_eval(row['genres']):
                temp_genre = genre(genre=genre_i['name'])
                #Check to see if genre already exists
                if session.query(genre).filter(genre.genre==genre_i['name']).count() == 0:
                    session.add(temp_genre)
                else:
                    #get existing identifier
                    temp_genre = session.query(genre).filter(genre.genre==genre_i['name'])[0]
                #populate junction table
                m_g = movie_genre(movie_id=temp_mov.movie_id, genre_id=temp_genre.genre_id)
                session.add(m_g)
           
            #Add names of production companies
            for prod_company_i in ast.literal_eval(row['production_companies']):
                temp_prod_company = prod_company(production_company=prod_company_i['name'])
                #Check to see if production company already exists
                if session.query(prod_company).filter(prod_company.production_company==prod_company_i['name']).count() == 0:
                    session.add(temp_prod_company)
                else:
                    #get existing identifier
                    temp_prod_company = session.query(prod_company).filter(prod_company.production_company==prod_company_i['name'])[0]
                #populate junction table
                m_p = movie_prod_company(movie_id=temp_mov.movie_id, prod_company_id=temp_prod_company.prod_company_id)
                session.add(m_p)
            
            session.commit()
            record_insert_count=record_insert_count + 1
    except Exception as e:
        #Prefer to send this error to some kind of error table where we can log
        print('Unable to insert %s with error: %s'%(row['title'], e))
        #flush session
        session.flush()

session.close()
print('%s new records added'%(record_insert_count))





##### Queries to answer requirements
##By Production Company
#budget per year
#revenue per year
#profit per year
#average popularity of produced movies per year
"""
SELECT 
    pc.production_company, 
    m.release_year,
    SUM(budget) as budget,
    SUM(revenue) as revenue,
    SUM(profit) as profit,
    AVG(popularity) as popularity
FROM production_company as pc
LEFT JOIN movie_prod_comp as mpc ON pc.prod_company_id = mpc.prod_company_id
LEFT JOIN movie as m ON m.movie_id = mpc.movie_id
GROUP BY
pc.production_company, m.release_year
"""
#releases by genre per year
"""
SELECT 
    pc.production_company, 
    m.release_year,
    g.genre,
    COUNT(*) as number_of_movies
FROM production_company as pc
LEFT JOIN movie_prod_comp as mpc ON pc.prod_company_id = mpc.prod_company_id
LEFT JOIN movie as m ON m.movie_id = mpc.movie_id
LEFT JOIN movie_genre as mg ON mpc.movie_id = mg.movie_id
LEFT JOIN genre as g ON g.genre_id = mg.genre_id
GROUP BY
pc.production_company, 
m.release_year,
g.genre
"""
##Movie Genre Details
#budget by genre by year
#revenue by genre by year
#profit by genre by year
"""
SELECT
g.genre,
m.release_year,
SUM(budget) as budget,
SUM(revenue) as revenue,
SUM(profit)
FROM genre as g
LEFT JOIN movie_genre as mg ON mg.genre_id = g.genre_id
LEFT JOIN movie as m ON m.movie_id = mg.movie_id
GROUP BY 
g.genre,
m.release_year
"""
#most popular genre by year
"""
WITH D1 AS
(SELECT
g.genre,
m.release_year,
AVG(popularity) as popularity
FROM genre as g
LEFT JOIN movie_genre as mg ON mg.genre_id = g.genre_id
LEFT JOIN movie as m ON m.movie_id = mg.movie_id
GROUP BY 
g.genre,
m.release_year) 

SELECT
    D1.genre,
    D1.release_year,
    D1.popularity
FROM D1
INNER JOIN (
    SELECT release_year, 
    MAX(popularity) as max_pop 
    FROM D1
    GROUP BY release_year
    ) AS D2 ON D1.release_year = D2.release_year
    AND D1.popularity = D2.max_pop
ORDER BY D1.release_year


"""