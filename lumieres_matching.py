import pandas as pd
from tqdm import tqdm
import json

import utils
import lumieres_api as lum


def matching_project(OriginalTitle,FrenchTitle,EnglishTitle,Director,country,refyear,ID,token):
    temp_res=[]

    #construction of the research parameters
    params=utils.search_params([OriginalTitle,FrenchTitle,EnglishTitle],Director,country,refyear)
    
    # search first with the most filters
    for p in params["title+director+country+year"]:
        mat=lum.find_movie(token,research_params=p)
        temp_res.append(
            {
                "ID" : ID,
                "recherche" : p,
                "resultat" : mat
            })

    # if all the results are empty (no film have been found) then eliminate some filters until someting is found
    param_choice=1 #set the parameters iterator to 1 as the first one have already been visited

    # here I add +[0] because params["title+director+country+year"] can be empty and then when arriving at this test there would be an error with max, and if it is empty then the max should be 0
    while param_choice<len(params) and max([len(k["resultat"]) for k in temp_res]+[0])==0 : 
        for p in params[list(params.keys())[param_choice]]:
            mat=lum.find_movie(token,research_params=p)
            temp_res.append({
                "ID" : ID,
                "recherche" : p,
                "resultat" : mat
            })
        param_choice+=1

    return temp_res


def matching_file(in_file,out_file,start_year=0,end_year=999999,show_progress=False):

    data=pd.read_excel(in_file)
    # here I split the data by year so that if there is an error, only one year is removed
    data_list=[data[data['refyear']==y].reset_index(drop=True) for y in range(max(start_year,data["refyear"].min()),min(end_year, data["refyear"].max())+1)]

    token=lum.get_token()

    if show_progress:
        iterable=tqdm(data_list)
    else:
        iterable=data_list()

    for df in tqdm(data_list):
        df['matching']=df.apply(lambda x: matching_project(x.OriginalTitle,x.FrenchTitle,x.EnglishTitle,x.Director,x.country1,x.refyear,x.ID,token), axis=1)

    lum.logout(token)

    concatenated_df = pd.concat(data_list, ignore_index=True).reset_index(drop=True)

    out_file = open(out_file, "w") 
    json.dump(concatenated_df.matching.to_list(), out_file, indent = 6) 
    out_file.close()

    return concatenated_df


def fill_back(data_file,matching_file,out_file):
    files=pd.read_excel(data_file)
    f = open(matching_file)
    data_m = json.load(f) 
    f.close() 
    start_year=int(data_m[0][0]["recherche"]["prod_start_year"]) #figure it out with matching file
    end_year= int(data_m[-1][-1]["recherche"]["prod_start_year"]) 
    filesliced=files[files['refyear']>=start_year ][files['refyear']<=end_year] 
    filesliced=filesliced.reset_index(drop=True)
    lumiere_ids=[]
    lumieres_title=[]
    lumieres_matching_title=[]
    lumieres_directors=[]
    lumieres_prod_year=[]
    lumieres_relevance=[]
    lumieres_admissions=[]
    imdb_id=[]

    for r in data_m:
        try:
            temp_result=utils.best_id(r)
        except:
            temp_result=-1
            print("error on most_found_id with arg : ",r)
        
        if type(temp_result)==int:
            lumiere_ids.append(-1)
            lumieres_title.append('')
            lumieres_matching_title.append('')
            lumieres_directors.append('')
            lumieres_prod_year.append(-1)
            lumieres_relevance.append(-1)
            lumieres_admissions.append(-1)
            imdb_id.append('')
        else:
            lumiere_ids.append(temp_result["id"])
            lumieres_title.append(temp_result["original_title"])
            lumieres_matching_title.append(temp_result["matching_title"])
            lumieres_directors.append(temp_result["directors"])
            lumieres_prod_year.append(temp_result["prod_year"])
            lumieres_relevance.append(temp_result["relevance"])
            lumieres_admissions.append(temp_result["total_admissions_obs"])
            imdb_id.append(temp_result["imdb_id"])

    filesliced["lumieres_id"]=lumiere_ids
    filesliced["lumieres_title"]=lumieres_title
    filesliced["lumieres_matching_title"]=lumieres_matching_title
    filesliced["lumieres_directors"]=lumieres_directors
    filesliced["lumieres_prod_year"]=lumieres_prod_year
    filesliced["lumieres_relevance"]=lumieres_relevance
    filesliced["lumieres_admissions"]=lumieres_admissions
    filesliced["imdb_id"]=imdb_id

    filesliced.to_excel(out_file,index=None)

    not_found=filesliced.loc[filesliced["lumieres_id"]==-1 ,:]
    last_slash= out_file.rfind("/")
    filename, extension = out_file[last_slash + 1:].split(".")
    not_found_file = out_file[:last_slash + 1] + f"{filename}_not_found.{extension}"
    not_found.to_excel(not_found_file,index=None)

    return filesliced
