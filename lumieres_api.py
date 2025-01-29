import requests as req
import json
import streamlit as st
# Diverse functions used to interact with the lumieres pro API
# You can find the API documentation here : https://lumierepro.obs.coe.int/schema/redoc


#exemple of valid format for the api movie search
movie_exemple={
    "title": "Microcosmos",                         # title should be at least 2 characters, can be an issue sometimes with one letter titles
    "director": "Claude	Nuridsany",
    "production_country": 'FR' ,                    # must always be only 2 characters, no more no less so it's one country at a time 
    "include_minority_coproducing_country": True,
    "prod_start_year": 1995,                        # every movies before this date will be excluded
}

#try to return a valid api identification token, if it can't it returns the reason
def get_token():
    gettokenurl='https://lumierepro.obs.coe.int/api/token'
    ##VERSION SANS STREAMLIT CLOUD
    # # the id for the lumiere pro api should be stored in a json format in a file named var.env that will be added to .gitignore
    # f=open("var.env",'r')
    # ident=json.load(f) 
    # f.close() 
    # rep=req.post(gettokenurl,json=ident)
    # try :
    #     return {'Authorization' : rep.headers["Authorization"]}
    # except:
    #     return (rep.reason)
    
    #VERSION AVEC STREAMLIT CLOUD 
    username=st.secrets["USERNAME"]
    password=st.secrets["PASSWORD"]
    ident= {
        "username" : username,
        "password" : password
    }

    rep=req.post(gettokenurl,json=ident)
    try :
        return {'Authorization' : rep.headers["Authorization"]}
    except:
        return (rep.reason)

#logs out from the api
def logout(token):
    rep=req.post("https://lumierepro.obs.coe.int/api/logout",headers=token)
    return rep.text


#makes a request to the lumieres api to search a movie, returns a dict with the api response
def movie_request(movie,token):
    apiurl="https://lumierepro.obs.coe.int/api/movies"

    rep=req.post(apiurl,json=movie,headers=token)
    try :
        return (rep.json())
    except:
        return (rep.reason)

#encapsulation of movie_request to simplify usage, handles token expiration problems
#in order to search for a movie you can either:
# - provide the information in the different arguments 
# - give a dict for research_params containing the movie search parameters
def find_movie(token,title=False,
                      director=False,
                      production_country=False,
                      prod_start_year=False,
                      prod_end_year=False,
                      exp_start_year=False,
                      exp_end_year=False,
                      research_params=False):
    
    if not research_params:
        movie=dict()
        if title:
            movie["title"]=title
        if director:
            movie["director"]=director
        if production_country:
            movie["production_country"]=production_country
        if prod_start_year:
            movie["prod_start_year"]=prod_start_year
        if prod_end_year:
            movie["prod_end_year"]=prod_end_year
        if exp_start_year:
            movie["exp_start_year"]=exp_start_year
        if exp_end_year:
            movie["exp_end_year"]=exp_end_year
    else:
        movie=research_params

    result=movie_request(movie,token)

    if type(result)==type('token is not valid'): #token is not valid <--very useful comment here
        new_token=get_token()
        if type(new_token)==type("can't get new token"):
            return "can't access api or create new token"
        else:
            token["Authorization"]=get_token()["Authorization"]
            
            result=movie_request(movie,token)
            return result
    else:
        return result


# returns the admissions information present in lumieres
# details : optionnal argument, if set to True (default) returns a dict with every admissions by year and country, on False it will return the sum of all admissions ever everywhere
def get_admissions(lumiere_id,token='no_token',details=True):
    apiurl="https://lumierepro.obs.coe.int/api/work/{0}/admissions".format(lumiere_id)

    if token=='no_token':
        token=get_token()

    rep=req.get(apiurl,headers=token)

    if type(rep)==type('token is not valid'): #token is not valid
        new_token=get_token()
        if type(new_token)==type("can't get new token"):
            return "can't access api or create new token"
        else:
            token["Authorization"]=get_token()["Authorization"]
            
            rep=req.get(apiurl,headers=token)
       
    try:
        rep_json= rep.json()
    except:
        return rep.reason

    if details:
        return rep_json
    else:
        if len(rep_json)==0:
            return -1
        
        adm=0
        for elt in rep_json:
            adm+=elt["admissions"]

        return adm

# returns a dict containing the external ids in lumieres for the provided movie using its id
def get_external_ids(lumiere_id,token='no_token'):
    apiurl="https://lumierepro.obs.coe.int/api/movie/{0}".format(lumiere_id)

    if token=='no_token':
        token=get_token()

    rep=req.get(apiurl,headers=token)

    if type(rep)==type('token is not valid'): #token is not valid
        new_token=get_token()
        if type(new_token)==type("can't get new token"):
            return "can't access api or create new token"
        else:
            token["Authorization"]=get_token()["Authorization"]
            
            rep=req.get(apiurl,headers=token)
    
    try:
        rep_json= rep.json()
    except:
        return rep.reason
    return rep_json["links"]