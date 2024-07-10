import numpy as np
import pandas as pd

#Diverse useful functions 

# returns the movie most found in the result of a matching
def best_id(matching):
    ids=dict()
    relevance_limit=0.7
    # count the number of times an id is found with a high enough relevance and the most found should be the best one
    for match in matching:
        for rr in match["resultat"]:
            
            if rr["id"]in ids.keys() and rr["relevance"]>=relevance_limit:
                ids[rr["id"]]+=1
            elif rr["relevance"]>=relevance_limit:
                ids[rr["id"]]=1
    if(len(ids)>0):
        found_id= max(ids,key=ids.get)
    else:
        return -1

    #now that we have the best id we search in our results for a successful match starting with the best searches using the most parameters
    for match in matching: 
        for rr in match["resultat"]:
            if rr["id"]==found_id:
                return rr
            
    return -1



# This function creates a dict with all the combinations of valid research parameters for our matching 
# Format :
#   - title : list of 3 string 'OriginalTitle','FrenchTitle','EnglishTitle' where the french and english titles can be nan
#   - director : list of X strings, as many elements as there is directors, should never be empty
#   - prod_country : list of all coproducing countries, can be nan
#   - prod_year : an int, should never be nan
# the order of the dict keys in the return dict is important as it is the order we should try to match the movie
def search_params(title,director,prod_country,prod_year):
    param_dict={
        "title+director+country+year" : [],
        "title+director+year" : [],
        "director+country+year" : [],
        "director+year" : [],
        "title+country+year" : [],
        "title+year" : [],
    }

    title= [t for t in set(title) if type(t)==str and len(t)>1] #remove nan values and titles like "U" that don't contain at least 2 characters (lumieres expects at least 2 char for title)
    prod_year_str=str(prod_year)
    
    for t in title :  
        for d in director:
            if type(prod_country)==list: # if there is at least one coproducing country 
                #the string in "production country" should not be more than 2 characters so it's one country at a time
                for c in prod_country:
                    temp_param={
                        "title": t,
                        "director": d,
                        "production_country": c[:2] , #limit to the first two characters if there is a weird country isocode that pops up
                        "include_minority_coproducing_country": True,
                        "prod_start_year": prod_year_str,
                    }
                    param_dict["title+director+country+year"].append(temp_param)
            
            # without production country 
            temp_param={
                "title": t,
                "director": d,
                "prod_start_year": prod_year_str,
            }
            param_dict["title+director+year"].append(temp_param)
    
    # without title
    for d in director:
        if type(prod_country)==list: # if there is at least one coproducing country
            for c in prod_country:
                temp_param={
                    "director": d,
                    "production_country": c[:2] ,
                    "include_minority_coproducing_country": True,
                    "prod_start_year": prod_year_str,
                }
                param_dict["director+country+year"].append(temp_param)
        
        # without production country and title
        temp_param={
            "director": d,
            "prod_start_year": prod_year_str,
        }
        param_dict["director+year"].append(temp_param)

    # without director /!\ this creates lost of false positive, but we can always filter out if the director is similar later
    for t in title :        
        if type(prod_country)==list: # if there is at least one coproducing country
            for c in prod_country:
                temp_param={
                    "title": t,
                    "production_country": c[:2] ,
                    "include_minority_coproducing_country": True,
                    "prod_start_year": prod_year_str,
                }
                param_dict["title+country+year"].append(temp_param)
        
        # without production country 
        temp_param={
            "title": t,
            "prod_start_year": prod_year_str,
        }
        param_dict["title+year"].append(temp_param)

    return param_dict

# removes the spaces that can be present at the beginning or end of a string
def remove_unnecessary_spaces(s):
    if type(s)==str:
        return s.strip()
    else:
        return s

# if the string is empty this will return nan
def remove_empty(s):
    if type(s)==str:
        if s=='':
            return np.nan
        else:
            return s
    else:
        return s