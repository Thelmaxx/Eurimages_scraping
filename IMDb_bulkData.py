import requests as req
import gzip as gz
import pandas as pd
import os
import imdb_scraping as imdb

from whoosh.analysis import StandardAnalyzer
from whoosh.index import create_in
from whoosh.fields import Schema, TEXT, ID, NUMERIC
from whoosh.qparser import MultifieldParser, FuzzyTermPlugin
from whoosh.query import And, Term, NumericRange


# Liste de stop words en anglais
stop_words = set([
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are", 
    "aren't", "aren't", "as", "at", "be", "because", "been", "before", "being", "below", "between", 
    "both", "but", "by", "can't", "cannot", "could", "couldn't", "did", "didn't", "does", "doesn't", 
    "don't", "down", "during", "each", "few", "for", "from", "had", "hadn't", "has", 
    "hasn't", "have", "haven't", "having", "here", "here's", "here's", "how", "how's", "how's", 
    "i", "i'm", "i've", "if", "in", "into", "is", "isn't", "it", "it's", "itself", "let", "more", 
    "most", "my", "myself", "of", "off", "on", "once", "only", "or", "other", "ought", "our", 
    "ours", "ourselves", "out", "over", "own", "same", "so", "than", "that", "that's", "that've", 
    "the", "theirs", "theirs", "them", "themselves", "then", "there", "there's", "there's", "therefore", 
    "these", "they", "they're", "they've", "this", "those", "through", "to", "under", "until", "up", 
    "very", "was", "wasn't", "were", "weren't", "what", "what's", "what's", "what's", "what's", "what's", 
    "when", "when's", "where", "where's", "which", "which's", "while", "who", "who's", "who's", "why", 
    "why's", "with", "won't", "would", "wouldn't"
])




##Appelle la fonction qui va chercher les données sur internet, et les range en un format utilisable:
##[{'imdb_id': 'tt0011801',
#   'originalTitle': 'Tötet nicht mehr',
#   'director': 'Lupu Pick',
#   'startYear': 2019.0},
#  {'imdb_id': 'tt0015414',
#   'originalTitle': 'La tierra de los toros',
#   'director': 'Musidora',
#   'startYear': 2000.0},
# ...
#  {'imdb_id': 'tt11668900',
#   'originalTitle': 'Tiga Setan Darah dan Cambuk Api Angin',
#   'director': 'Liliek Sudjio',
#   'startYear': 1988.0},
#  ...]
def bulk_data():
    print("test")

    tit_basics=imdb.get_title_basics('data/test_title_basics.tsv')
    tit_basics['startYear'] = pd.to_numeric(tit_basics['startYear'], errors='coerce') ##permet de filtrer par date ensuite, et de gagner du temps
    tit_crew=imdb.get_title_crew('data/test_title_crew.tsv')
    name=imdb.get_name_basics('data/test_name_bascis.tsv')
    print("testest1")
    # Filter data, then merge into a single table
    tit_basics_filtered=tit_basics[(tit_basics['isAdult']==0) & (tit_basics['titleType']=="movie") & (tit_basics["startYear"]>=1980)]
    merged=tit_basics_filtered.merge(tit_crew, on="tconst", how="inner")
    merged = merged.reset_index()
    merged
    final = merged.merge(name, left_on="directors", right_on="nconst", how="left",suffixes=('', '_name'),indicator=True) #left : garde les films même si le réal n'est pas trouvé
    final['primaryName'].fillna('Unknown', inplace=True)
    final = final.rename(columns={
        "tconst": "imdb_id",
        "primaryName": "director"
    })
    final['originalTitle'].fillna('Unknown', inplace=True) #We replace the NaN values in the “originalTitle” column with Unknown to avoid errors later on.

    movies = final[["imdb_id", "originalTitle", "director", "startYear"]].to_dict(orient="records") 

    print("on y est ?")
    return movies


##créer un index lisible par Whoosh pour effectuer la recherche
def create_index(movies):

    schema_imdb = Schema(
        imdb_id=ID(stored=True),
        originalTitle=TEXT(stored=True),
        director=TEXT(stored=True),
        startYear=NUMERIC(stored=True)
    )

    # Étape 2 : Créer un index
    if not os.path.exists("book_index_imdb"):
        os.mkdir("book_index_imdb")
    index = create_in("book_index_imdb", schema_imdb)

    # Ajouter des documents (livres) à l'index
    writer = index.writer()

    imdb_movies = movies
    i=0
    try :
        for movie in imdb_movies:
            str_start_year = (
                int(movie["startYear"])
                if (movie["startYear"] and movie["startYear"] != r"\N")
                else -1
            )

            # originalTitle_corr=movie["originalTitle"] if movie["originalTitle"] else "Unknown"
            # if i == 73179:
            #     print(movie["originalTitle"])
            #     print(type(originalTitle_corr))

            writer.add_document(
                imdb_id=movie["imdb_id"],
                originalTitle=movie["originalTitle"],
                director=movie["director"],
                startYear=str_start_year
            )
            i+=1
        writer.commit()
    except Exception as e:
        writer.commit()
        print(f"Erreur : {e}")
        print(i)


def prepare_fuzzy_query(query_string):
    # Ajouter ~ à chaque mot de la requête
    terms = query_string.split()
    fuzzy_terms = [term + "~" if term.lower() not in stop_words else term for term in terms]
    return " ".join(fuzzy_terms)


# Recherche dans l'index
def search_books(query_string,min_publication_date,index):
    with index.searcher() as searcher:
        # Permet de chercher dans plusieurs champs
        parser = MultifieldParser(["originalTitle", "director"], schema=index.schema)
        parser.add_plugin(FuzzyTermPlugin())  # Ajouter la recherche floue

        fuzzy_query_string = prepare_fuzzy_query(query_string)
        query = parser.parse(fuzzy_query_string)
        
        # Créer un filtre pour la date de publication
        date_filter = NumericRange("startYear", min_publication_date, None)  # None pour pas de limite supérieure

        results = searcher.search(query,date_filter)
        print(f"Résultats trouvés : {len(results)}")
        print(f"Votre recherche : {query}")
        for result in results:
            #print(f"Titre : {result['title']}, Auteur : {result['author']}, Date : {result['publication_date']}")
            print(result)
            print(type(result))

def multi_search_books(query_title,query_director,min_publication_date,index):
    with index.searcher() as searcher:
        # Permet de chercher dans plusieurs champs
        title_parser = MultifieldParser(["originalTitle"], schema=index.schema)
        director_parser = MultifieldParser(["director"], schema=index.schema)
        title_parser.add_plugin(FuzzyTermPlugin())  # Ajouter la recherche floue
        director_parser.add_plugin(FuzzyTermPlugin())  # Ajouter la recherche floue
        fuzzy_query_title = prepare_fuzzy_query(query_title)
        fuzzy_query_director = prepare_fuzzy_query(query_director)
        query_title = title_parser.parse(fuzzy_query_title)
        query_director = director_parser.parse(fuzzy_query_director)

        combined_query = And([query_title, query_director])

        #filtre pour la date de publication
        date_filter = NumericRange("startYear", min_publication_date, None)  # None pour pas de limite supérieure
        
        results = searcher.search(combined_query,date_filter)
        print(f"Résultats trouvés : {len(results)}")
        print(f"Votre recherche : {combined_query}")
        for result in results:
            #print(f"Titre : {result['title']}, Auteur : {result['author']}, Date : {result['publication_date']}")
            print(result)
            print(type(result))
    