import streamlit as st
import numpy as np
import lumieres_api as lum
import lumieres_matching as lumatch
import pandas as pd
import pyodbc 
import platform


token=lum.get_token()

if platform.system()=="Windows":
    driver="SQL Server"
else:
    driver = "/opt/microsoft/msodbcsql17/lib64/libmsodbcsql-17.so"  # Driver Linux

cnxn = pyodbc.connect(f"Driver={driver};"
                        "Server=LAPTOP-IUA12HD6\SQLSERVER2;"
                        "Database=Coeurimages;"
                        "Trusted_Connection=yes;")

cursor = cnxn.cursor()

st.set_page_config(layout="wide")

st.title("LUMIERE scraping 🎬")


if "resultat_data" not in st.session_state:
    st.session_state.resultat_data = []
if "selected_films" not in st.session_state:
    st.session_state.selected_films = []


# Liste des isocodes prédéfinis
isocodes_list = [
    "AD - Andorra","AE - United Arab Emirates","AF - Afghanistan","AG - Antigua and Barbuda","AL - Albania","AM - Armenia","AO - Angola",
    "AR - Argentina","AT - Austria","AU - Australia","AZ - Azerbaijan","BA - Bosnia-Herzegovina","BB - Barbados","BE - Belgium","BF - Burkina Faso",
    "BG - Bulgaria","BH - Bahrain","BJ - Benin","BN - Brunei","BO - Bolivia","BR - Brazil","BW - Botswana","BY - Belarus","BZ - Belize","CA - Canada",
    "CD - Congo (Democratic Republic of Congo)","CF - Central African Republic","CH - Switzerland","CI - Ivory Coast","CL - Chile",
    "CM - Cameroon","CN - China","CO - Colombia","CR - Costa Rica","CS - Serbia and Montenegro (1993-2006)","CU - Cuba","CY - Cyprus","CZ - Czechia",
    "DE - Germany","DK - Denmark","DZ - Algeria","EC - Ecuador","EE - Estonia","EG - Egypt","ES - Spain","ET - Ethiopia","FI - Finland",
    "FR - France","GA - Gabon","GB - United Kingdom","GE - Georgia","GH - Ghana","GM - Gambia","GN - Guinea","GQ - Equatorial Guinea",
    "GR - Greece","GT - Guatemala","HK - Hong Kong (CN)","HN - Honduras","HR - Croatia","HT - Haiti","HU - Hungary","ID - Indonesia",
    "IE - Ireland","IL - Israel","IN - India","IR - Iran","IS - Iceland","IT - Italy","JM - Jamaica","JO - Jordan","JP - Japan","KE - Kenya",
    "KG - Kyrgyzstan","KH - Cambodia","KP - Korea (Democratic People's Republic of)","KR - South Korea","KW - Kuwait","KZ - Kazakhstan","LB - Lebanon","LI - Liechtenstein",
    "LK - Sri Lanka","LS - Lesotho","LT - Lithuania","LU - Luxembourg","LV - Latvia","LY - Libya","MA - Morocco","MC - Monaco",
    "MD - Moldova","ME - Montenegro (from 2006)","MG - Madagascar","MK - North Macedonia","ML - Mali","MR - Mauritania","MT - Malta",
    "MW - Malawi","MX - Mexico","MY - Malaysia","MZ - Mozambique","NA - Namibia","NE - Niger","NG - Nigeria","NI - Nicaragua","NL - Netherlands",
    "NO - Norway","NP - Nepal","NZ - New Zeland","OM - Oman","PA - Panama","PE - Peru","PH - Philippines","PK - Pakistan","PL - Poland",
    "PR - Puerto Rico (US)","PS - Palestinian Territories","PT - Portugal","PY - Paraguay","QA - Qatar","RO - Romania","RS - Serbia",
    "RU - Russian Federation","RW - Rwanda","SA - Saudi Arabia","SD - Sudan","SE - Sweden","SG - Singapore","SI - Slovenia","SK - Slovakia",
    "SL - Sierra Leone","SM - San Marino","SN - Senegal","SO - Somalia","SV - El Salvador","SY - Syrian Arab Republic","TG - Togo",
    "TH - Thailand","TJ - Tajikistan","TM - Turkmenistan","TN - Tunisia","TR - Repulic of Türkiye","TT - Trinidad and Tobago","TW - Taiwan",
    "TZ - Tanzania","UA - Ukraine","UG - Uganda","US - United States of America","UY - Uruguay","UZ - Uzbekistan","VA - Holy See","VE - Venezuela",
    "VN - Vietnam","XK - Kosovo","YE - Yemen","ZA - South Africa","ZM - Zambia","ZW - Zimbabwe"
                ]


dir=[]
country=[]


st.write("### One movie")
col1,col2 = st.columns(2)
with col1:
    tit1=st.text_input("Title 1")
    tit2=st.text_input("Title 2")
    #oth_title=st.text_input("Other Title?")
    dir_tmp=st.text_input("Director")
with col2:
    selected_isocodes = st.multiselect(
        label="Country",
        options=isocodes_list,
        default=[]  # Valeurs par défaut
    )
    country=[i[:2] for i in selected_isocodes]
    id=st.text_input("Coeurimages ID (Give the information to the database)")
    ryear=st.number_input("Production years from *", value=1950) ##### échanger avec st.number_input(...)
    reference=""
relevance_condition=st.slider("What degree of relevance (%) do you want the results to have?", min_value=0, max_value=100, value=95)*1/100

if id:  # Vérifie si un ID a été saisi
    # Requête SQL pour récupérer la référence
    query = "SELECT Reference FROM Files WHERE ID = ?"
    cursor.execute(query, id)
    result = cursor.fetchone()
        
    # Vérification du résultat
    if result:
        reference = result[0]
        st.success(f"La référence associée à l'ID {id} est : {reference}")
    else:
        st.error(f"Aucune référence trouvée pour l'ID {id}.")

if len(dir_tmp)>1:
    #dir.append(dir_tmp) #Remplis dir uniquement si au moins 2 caractères, sinon liste vide (ne renvoie pas d'erreur)
    dir = [d.strip() for d in dir_tmp.split(",")]

if st.button("Valider les critères"):
    st.session_state.resultat_data=[]
    # Vérifier si les champs obligatoires sont remplis
    if not ryear:
        st.error("Veuillez remplir tous les champs obligatoires (*) avant de continuer 😎")
    else:
        if not id:
            st.warning("If you do not provide a Coeurimages identifier, the film will not be linked to Coeurimages data.")
        res=lumatch.matching_project(tit1,tit2,"",dir,country,ryear,id,token) #res est une liste de dictionnaires

        #st.write("### Results :")
        #st.write("-----------------------------")

        for movie in res:
            
            for result in movie["resultat"]:
                
                # res_id=result["id"]
                # res_tit=result["original_title"]
                # res_imdb=result["imdb_id"]
                # res_adm=result["total_admissions_obs"]
                # res_year=result["prod_year"]
                # res_country=result["production_countries"]
                res_relevance=result["relevance"]
                # res_director=result["directors"]
                if res_relevance>=relevance_condition:
                    #st.write(result)
                    st.session_state.resultat_data.append(result) 

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
    st.write("### Sélectionnez les films à garder")
    #col3,col4=st.columns([1,20])  
    for i, movie in enumerate(st.session_state.resultat_data):
        #id_movie=movie["id"]
        tit_movie=movie["original_title"]
        dir_movie=movie["directors"]
        rel_movie=movie["relevance"]
        year_movie=movie["prod_year"]
        adm_movie=movie["total_admissions_obs"]
        imdb_id=movie["imdb_id"]
        country_movie=movie["production_countries"]
        # st.markdown(
        #     """
        #     <style>
        #     /* Ajouter un espace au-dessus de la première checkbox */


        #     /* Modifier l'espace entre chaque checkbox*/
        #     .stCheckbox {
        #         margin-top: 8px; 
        #         margin-bottom: px; /*Valeur espacement*/
        #     }
        #     </style>
        #     """,
        #     unsafe_allow_html=True
        # )
        #with col3 :
        is_selected=st.checkbox(
            #label="",
            label=f"*{tit_movie}*, {dir_movie}, {year_movie}, **Countries**: {country_movie} ({rel_movie*100}%) " ,
            value=(rel_movie == 1.0),
            key=f"film_{i}"
        )
        
        #  with col4:
        #     if i==0:  # Pour modifier l'espace au dessus du premier label seulement
        #         st.markdown(f"""
        #             <div style="font-size:22px; margin-top:5px; margin-bottom:12.8px;">
        #                 <i>{tit_movie}</i>, 
        #                 {dir_movie}, 
        #                 {year_movie},
        #                 <b>Countries</b>: {country_movie}
        #                 (<span style="color:orange;">{rel_movie * 100}%</span>)
        #             </div>
        #         """, unsafe_allow_html=True)
        #     else:
        #         st.markdown(f"""
        #             <div style="font-size:22px; margin-bottom:12.8px;">
        #                 <i>{tit_movie}</i>, 
        #                 {dir_movie}, 
        #                 {year_movie},
        #                 <b>Countries</b>: {country_movie}
        #                 (<span style="color:orange;">{rel_movie * 100}%</span>)
        #             </div>
        #         """, unsafe_allow_html=True)

            # st.markdown(f"""
            #     <div style="font-size:22px; margin-bottom: 10px;">
            #         <i>{tit_movie}</i>, 
            #         {dir_movie}, 
            #         {year_movie},
            #         <b>Countries</b>: {country_movie}
            #         (<span style="color:orange;">{rel_movie * 100}%</span>)
            #     </div>
            # """, unsafe_allow_html=True)

        # Si la case est cochée, ajouter à la liste des films sélectionnés
        if is_selected and movie["id"] not in st.session_state.selected_films:
            st.session_state.selected_films.append(movie["id"])
        # Si la case est décochée, retirer de la liste
        elif not is_selected and movie["id"] in st.session_state.selected_films:
            st.session_state.selected_films.remove(movie["id"]) 



insert_query=''' INSERT INTO test3_TableID (FileID, Reference, lum_id, imdb_id)
              VALUES (?, ?, ?, ?);'''

if st.button("Envoyer dans la base de données"):
    if st.session_state.selected_films:
        selected_data = [movie for movie in st.session_state.resultat_data if movie["id"] in st.session_state.selected_films]
        idx=0
        for resultat in selected_data:
            #st.write(resultat)
            values=(id, reference, resultat['id'], resultat['imdb_id'])
            cursor.execute(insert_query,values)
            cnxn.commit()
            idx+=1
        st.success(f"Données sur {idx} films envoyées dans base de données ! 📲")
        cursor.close()
        cnxn.close()