import streamlit as st
import numpy as np
import lumieres_api as lum
import lumieres_matching as lumatch
import pandas as pd
import pyodbc 
token=lum.get_token()

def smaller_index(liste):
    number = 0
    while number in liste:
        number += 1
    return number

st.set_page_config(layout="wide")



st.title("LUMIERE scraping 🎬")


if "resultat_data" not in st.session_state:
    st.session_state.resultat_data = []
if "selected_films" not in st.session_state:
    st.session_state.selected_films = []
if "processed_lines" not in st.session_state:
    st.session_state.processed_lines = []
# if "display_counter" not in st.session_state:
#     st.session_state.display_counter = 0
if "refresh_trigger" not in st.session_state:
    st.session_state.refresh_trigger = False
if "start_index" not in st.session_state:
    st.session_state.start_index = 0


###############################################################################################################################


films_per_page = 5 
start_index = smaller_index(st.session_state.processed_lines)
end_index =  films_per_page + len(st.session_state.processed_lines)
#example beggining : [start_index:end_index]=[0:10] --> the last excluded
dir=[]
country=[]
title=""

with st.sidebar:
    if st.button("↻ | Clean"):
        st.session_state.refresh_trigger = True
st.write("## Import an Excel file")
col1,col2=st.columns(2)
with col1:

    uploaded_file = st.file_uploader("Select an Excel file", type=["xlsx","xls"])
    films_per_page = st.number_input("Maximum number of projects displayed at once (more than 10 not recommended) :",value=5)
    max_lines= st.number_input("Maximum number of results displayed per film :",value=30)

with col2:
    relevance_condition=st.slider("What degree of relevance (%) do you want the results to have?", min_value=0, max_value=100, value=95)*1/100

start_index = smaller_index(st.session_state.processed_lines)
end_index =  films_per_page + len(st.session_state.processed_lines)
#example beggining : [start_index:end_index]=[0:10] --> the last excluded

if uploaded_file is not None:
    # Read Excel file with pandas
    try:
        df = pd.read_excel(uploaded_file)
        #st.success("File loaded successfully 🥳")
    except Exception as e:
        st.error(f"Error reading file : {e}")
    else:
        nb_lines=df.shape[0]
        if df.columns.tolist() == ["line","ID","title1","title2","director","country","refyear"]:
            with col2:
                # Display data overview
                st.write("###### Data overview :")
                st.write(df.head())  # Display 5 first lines
            # with col1:
            #     st.write(f'Number of displayed results: {nb_lines - st.session_state.display_counter}')

            if df["ID"].isnull().any() or (df["ID"].astype(str).str.strip() == "").any():
                st.warning("If you do not provide a Coeurimages identifier, the film in question will not be linked to Coeurimages data.")

            for index, row in df.iloc[start_index:end_index].iterrows():
                if index in st.session_state.processed_lines:
                    continue
                st.session_state.resultat_data=[]
                cnxn = pyodbc.connect("Driver={SQL Server};"
                        "Server=LAPTOP-IUA12HD6\SQLSERVER2;"
                        "Database=Coeurimages;"
                        "Trusted_Connection=yes;")

                cursor = cnxn.cursor()
                row=row.to_dict()
                for key,value in row.items():
                    if pd.isna(value):
                        row[key] = ""
                line_nb=row["line"]
                id=row["ID"]
                title1=row["title1"]
                title2=row["title2"]
                #eng_title=row["english_title"]
                dir_tmp=row["director"]
                country_tmp=row["country"]
                ryear=row["refyear"]
                reference=""
            ###############################################################################################################################
                if id:  # Vérifie si un ID a été saisi
                    # Requête SQL pour récupérer la référence
                    query = "SELECT Reference FROM Files WHERE ID = ?"
                    cursor.execute(query, id)
                    result = cursor.fetchone()
                        
                    # Vérification du résultat
                    if result:
                        reference = result[0]
                    #     st.success(f"La référence associée à l'ID {int(id)} est : {reference}")
                    # else:
                    #     st.error(f"Aucune référence trouvée pour l'ID {int(id)}.")


                if len(dir_tmp)>1:
                    dir = [d.strip() for d in dir_tmp.split(",")]
                    #dir.append(dir_tmp) #Remplis dir uniquement si au moins 2 caractères, sinon liste vide (ne renvoie pas d'erreur)
                if len(country_tmp) >1:
                    country= [cou.strip() for cou in country_tmp.split(",")]

    
                # Vérifier si les champs obligatoires sont remplis
                if not ryear:
                    ryear=1950
                
                title = title1 if title1 else title2

                if reference:
                    st.markdown(f"### Line n°{line_nb} <span style='color: orange;'>'{title}'</span> (Reference : {reference})", unsafe_allow_html=True)
                else:
                    st.markdown(f"### Line n°{line_nb} <span style='color: orange;'>'{title}'</span> (No reference found)", unsafe_allow_html=True)
                # if not id:
                #     st.warning("If you do not provide a Coeurimages identifier, the film will not be linked to Coeurimages data.")
                res=lumatch.matching_project(title1,title2,"",dir,country,ryear,id,token) #res est une liste de dictionnaires


                #st.write(res)
                i=0
                for movie in res:
                    for result in movie["resultat"]:
                        res_id=result["id"]
                        res_tit=result["original_title"]
                        res_imdb=result["imdb_id"]
                        res_adm=result["total_admissions_obs"]
                        res_year=result["prod_year"]
                        res_country=result["production_countries"]
                        res_relevance=result["relevance"]
                        res_director=result["directors"]
                        if res_relevance>=relevance_condition:
                            i+=1
                            st.session_state.resultat_data.append(result)
                if i==0:
                    #st.write("No matching results were found 😢")
                    st.markdown(
                        "<span style='color:red;'>No matching results were found</span>", 
                        unsafe_allow_html=True
                    )

                # ###Unifie les résultats en gardant la dernière occurence d'un même film (lumiere id)
                # unique_results = {result["id"]: result for result in st.session_state.resultat_data}
                # st.session_state.resultat_data = list(unique_results.values()) #Avoiding duplication caused by the LUMIERE API search method

                ###Unifie les résultats en gardant l'occurence d'un même film ayant reçu le plus haut score de pertinence
                unique_results = {}
                for result in st.session_state.resultat_data:
                    film_id = result["id"]
                    if film_id not in unique_results or result["relevance"] > unique_results[film_id]["relevance"]:
                        unique_results[film_id] = result
                st.session_state.resultat_data = list(unique_results.values())


                def country_match_score(production_countries, country_list):
                    countries = [c.strip() for c in production_countries.split(",")] # Convert "FR, IT" to ["FR", "IT"]
                    return sum(1 for c in countries if c in country_list) #number of common country
                    
                #sorts first by relevance, then by the number of countries corresponding to the user's input
                st.session_state.resultat_data = sorted(st.session_state.resultat_data, key=lambda x: (x["relevance"], country_match_score(x["production_countries"], country)), reverse=True)


                ####CHECKBOXES

                

                ##Création + Sélection checkboxes
                if st.session_state.resultat_data:
                    st.write("##### Select films to save")
        
                    for i, movie in enumerate(st.session_state.resultat_data[:max_lines]): ##I could select the first items here because the list is already sorted by relevance
                        id_movie=movie["id"]
                        tit_movie=movie["original_title"]
                        dir_movie=movie["directors"]
                        rel_movie=movie["relevance"]
                        year_movie=movie["prod_year"]
                        adm_movie=movie["total_admissions_obs"]
                        imdb_id=movie["imdb_id"]
                        country_movie=movie["production_countries"]
                        is_selected=st.checkbox(
                            label=f"**Original Title**: *{tit_movie}*, **Directors**: *{dir_movie}*, **Start year**: *{year_movie}*, **Producing countries**: *{country_movie}*, **IMDb ID** : *{imdb_id}*, **Relevance**: *{rel_movie*100}%*" ,
                            value=(rel_movie == 1.0),
                            key=f"film_{index}_{i}"
                        )
                        # Si la case est cochée, ajouter à la liste des films sélectionnés
                        if is_selected and movie["id"] not in st.session_state.selected_films:
                            st.session_state.selected_films.append(movie["id"])
                        # Si la case est décochée, retirer de la liste
                        elif not is_selected and movie["id"] in st.session_state.selected_films:
                            st.session_state.selected_films.remove(movie["id"]) 
                        nb_movie=i+1
                    #st.write(nb_movie)
                


                insert_query=''' INSERT INTO test3_TableID (FileID, Reference, lum_id, imdb_id)
                            VALUES (?, ?, ?, ?);'''

                #st.write(st.session_state.selected_films)
                col3,col4,col5=st.columns([1,1,9])
                with col3:
                    if st.button("Validate",key=index):
                        if st.session_state.selected_films:
                            selected_data = [movie for movie in st.session_state.resultat_data if movie["id"] in st.session_state.selected_films]
                            if selected_data:
                                idx=0
                                for resultat in selected_data:
                                    #st.write(resultat)
                                    values=(id, reference, resultat['id'], resultat['imdb_id'])
                                    cursor.execute(insert_query,values)
                                    cnxn.commit()
                                    idx+=1
                                st.success(f"Data sent to database ! 📲")
                                st.session_state.processed_lines.append(index) #Mark line as processed
                                # st.session_state.display_counter += 1
                            else:
                                st.warning("No films selected! 🐲")
                            cursor.close()
                            cnxn.close()
                            st.rerun()

                with col4:
                    if st.button("Discard",key=f"discard_{index}"):
                        st.session_state.processed_lines.append(index) #Mark line as processed
                        st.rerun()
                        

                st.write("-----------------------------")

                dir=[]
                country=[]

        else :
            st.error("The excel file is not readable (pay attention to column names: line, ID, title2, title2, director, country, refyear).")
                



