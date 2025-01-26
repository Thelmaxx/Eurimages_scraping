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

# with st.sidebar:
#     if st.button("↻ | Clean"):
#         st.session_state.refresh_trigger = True
st.write("## Choose parameters")
col1,col2=st.columns(2)
with col1:
    start_year = st.number_input('Min year :',value=2018)
    end_year = st.number_input('Max year :',value=2020)
    films_per_page = st.number_input("Maximum number of projects displayed at once (more than 10 not recommended) :",value=5)
    max_lines= st.number_input("Maximum number of results displayed per film :",value=30)

with col2:
    relevance_condition=st.slider("What degree of relevance (%) do you want the results to have?", min_value=0, max_value=100, value=95)*1/100

start_index = smaller_index(st.session_state.processed_lines)
end_index =  films_per_page + len(st.session_state.processed_lines)
#example beggining : [start_index:end_index]=[0:10] --> the last excluded

conn = pyodbc.connect("Driver={SQL Server};"
        "Server=LAPTOP-IUA12HD6\SQLSERVER2;"
        "Database=Coeurimages;"
        "Trusted_Connection=yes;")

query = f"""
WITH RankedFS AS (
    SELECT 
        fs.FileId, 
        fs.FinancialStructureCodeId, 
        fs.CoproducerId,
        fs.AnnouncedAmount,
        RANK() OVER (PARTITION BY fs.FileId ORDER BY fsc.TranslationID DESC) AS row_priority --Gives priority to the largest available TranslationID (2304 ('FP4') otherwise 2303 otherwise 2302 otherwise 2301)
    FROM 
        [CoeurImages].[dbo].[FinancialStructure] as fs
	left join CoeurImages.dbo.FinancialStructureCode as fsc ON fs.FinancialStructureCodeId=fsc.ID
    WHERE 
        fsc.TranslationID IN ('2304', '2303', '2302', '2301') --Takes only the rows linked to FP4, FP3, FP2, FP1
),
DirectorsCTE AS (
    SELECT 
        fil.ID AS FileId,
        STRING_AGG( ISNULL(p.Firstname, '') + ' ' + ISNULL(p.Lastname, ''), ',') as director
    FROM 
        [CoeurImages].[dbo].[Files] AS fil
    LEFT JOIN 
        [CoeurImages].[dbo].[FilePartner] AS fp ON fil.ID = fp.FileId
    LEFT JOIN 
        [CoeurImages].[dbo].[Role] AS r ON fp.RoleId = r.ID
    LEFT JOIN 
        [CoeurImages].[dbo].[Partner] AS p ON fp.PartnerId = p.ID
    WHERE 
        r.TranslationID = '1707'
    GROUP BY 
        fil.ID
)

SELECT  ROW_NUMBER() OVER (ORDER BY (SELECT NULL)) AS line
		,[ID]  
        ,max([OriginalTitle]) as [title]
		,max(director) as director
 		,CONCAT_WS(',', max(country_1), max(country_2), max(country_3), max(country_4), max(country_5), max(country_6), max(country_7), max(country_8), max(country_9), max(country_10)) AS country
		,max(refyear) as refyear
		,max(support) as support
		,max(Reference) as Reference
		,max(MeetingId) as MeetingId




FROM(

	SELECT [ID]
			,max(Reference) as Reference
			,max(MeetingId) as MeetingId
			,max(refyear) as refyear
			,max([OriginalTitle]) as [OriginalTitle]
			,max(director) as director
			,max(support) as support
			,MAX(CASE WHEN contributor_rank = 1 THEN country1 END) AS country_1
			,MAX(CASE WHEN contributor_rank = 2 and percentage_participation>0 THEN country1 END) AS country_2
			,MAX(CASE WHEN contributor_rank = 3 and percentage_participation>0 THEN country1 END) AS country_3
			,MAX(CASE WHEN contributor_rank = 4 and percentage_participation>0 THEN country1 END) AS country_4
			,MAX(CASE WHEN contributor_rank = 5 and percentage_participation>0 THEN country1 END) AS country_5
			,MAX(CASE WHEN contributor_rank = 6 and percentage_participation>0 THEN country1 END) AS country_6
			,MAX(CASE WHEN contributor_rank = 7 and percentage_participation>0 THEN country1 END) AS country_7
			,MAX(CASE WHEN contributor_rank = 8 and percentage_participation>0 THEN country1 END) AS country_8
			,MAX(CASE WHEN contributor_rank = 9 and percentage_participation>0 THEN country1 END) AS country_9
			,MAX(CASE WHEN contributor_rank = 10 and percentage_participation>0 THEN country1 END) AS country_10


	FROM(

	SELECT  fil.ID
			,max(d.director) as director
			,max([Reference]) as Reference
			,max(fil.NextMeetingId) as MeetingId
			,
			CASE 
			WHEN max(LEFT(Reference,2))>80 
	    		THEN Cast('19'+max(LEFT(Reference,2)) as int)
				ELSE Cast('20'+max(LEFT(Reference,2)) as int)
				END
			as refyear
		   ,max([OriginalTitle]) as [OriginalTitle]

		  ,CASE
			WHEN max(trans_comdec.TranslatedText)=' '
			THEN CASE 
					WHEN max(trans_secr.TranslatedText)='Eligible'
					THEN 'Pending support decision'
					ELSE 'Inelegible'
				 END
			ELSE max(trans_comdec.TranslatedText)
			END as support

		  ,CASE 
				when max(fsa.budget_fpmax)>0 
				then round(sum(CASE WHEN rfs.row_priority=1 THEN rfs.AnnouncedAmount ELSE 0 END)/max(fsa.budget_fpmax),5)
				else NULL
		   END as percentage_participation
		  --in case of equality of biggest sum(fs.AnnouncedAmount), the majority coprod is the delegate coproducer, but if the 2 biggest are equal and a smaller one is delegate then both 2 biggest are majority
		  --ROW_NUMBER is chosen to avoid the disappearance of a country when minority countries have the same amount of participation (their respective ranks are then distributed at random)
		  ,ROW_NUMBER() OVER(PARTITION BY fil.ID ORDER BY sum(CASE WHEN rfs.row_priority=1 THEN rfs.AnnouncedAmount ELSE 0 END) DESC, max(fpart.is_delegate_producer) DESC) as contributor_rank 


		  ,max(RTRIM(cou.IsoCode)) as country1
		  


	FROM [CoeurImages].[dbo].[Files] as fil

				left join DirectorsCTE as d on fil.ID = d.FileId

				left join [CoeurImages].[dbo].[FilePartner] as fp on fil.ID=fp.FileId
				left join [CoeurImages].[dbo].[Role] as r on fp.RoleId=r.ID
				left join [CoeurImages].[dbo].[Partner] as p on fp.PartnerId=p.ID
				

				left join [CoeurImages].[dbo].[Meeting] as me ON fil.NextMeetingId=me.Id
  
				--Committee Decision
				left join CoeurImages.dbo.CommitteeDecision as comdec 
				left join (Select * from CoeurImages.dbo.Translation where LanguageId='EN') as trans_comdec
				on comdec.TranslationId=trans_comdec.ID 
				on fil.CommitteDecisionId=comdec.Id 
  
				--Secretariat Decision
				left join Coeurimages.dbo.SecretariatDecision as secr
				left join (Select * from CoeurImages.dbo.Translation where LanguageId='EN') as trans_secr 
				on secr.TranslationId=trans_secr.ID
				on fil.SecretariatDecisionID=secr.ID

  
				--financial structure and FP1 selection
				left join RankedFS as rfs on fil.ID=rfs.FileId
				left join CoeurImages.dbo.FinancialStructureCode as fc on rfs.FinancialStructureCodeId=fc.ID
				left join (Select * from CoeurImages.dbo.Translation where LanguageId='EN') as trans_fc on fc.TranslationID=trans_fc.ID

				-- country
				left join CoeurImages.dbo.Partner as part on rfs.CoproducerId=part.ID
				left join CoeurImages.dbo.Country as cou on part.CountryID=cou.ID
				left join CoeurImages.dbo.Country as cou2 on part.Country2ID=cou2.ID

				-- genre
				left join ([CoeurImages].[dbo].[FilmGenreTheme] as theme 
				right join [CoeurImages].[dbo].[FilmGenre] as genre 
				on theme.Id=genre.FilmGenreThemeId) 
				on fil.GenreId=genre.Id

				-- kind
				left join
		  		[CoeurImages].[dbo].[FilmKind] as fk
				on fil.KindId=fk.ID
				left join 
		  		(Select * from CoeurImages.dbo.Translation where LanguageId='EN') as trans_kind
				on fk.TranslationID = trans_kind.ID


				  --Majority/minority precisions using the delegate producer for equality cases, fpart.RoleID=7 for delegate producer
				left join (Select 
							FileID,
							PartnerId
							,COUNT(CASE WHEN RoleId=7 THEN 1 END) as is_delegate_producer
							From CoeurImages.dbo.FilePartner 
							group by FileId,PartnerId
							)
				as fpart on rfs.CoproducerId= fpart.PartnerId and fil.ID=fpart.FileId


				 --budget calculation
				left join
				(
				SELECT  [FileId]
			 		,sum(rfs.AnnouncedAmount) as budget_fpmax

				FROM RankedFS as rfs
				left join CoeurImages.dbo.FinancialStructureCode as fsc
				left join (Select * from CoeurImages.dbo.Translation where LanguageId='EN') as transfsc
				on fsc.TranslationID=transfsc.ID
				on rfs.FinancialStructureCodeId=fsc.ID

				where (transfsc.TranslatedText like '%FP %' or transfsc.TranslatedText like '%PF %') and rfs.row_priority=1

				group by FileId
			   ) as fsa
			   on fil.ID=fsa.FileId


			 where 
			 r.TranslationID='1707' and trans_fc.TranslatedText like '%FP %'
			 group by fil.ID
					,rfs.CoproducerId
					,d.director
	) as coprordre
	GROUP BY ID
) as listcountries
WHERE refyear BETWEEN {start_year} AND {end_year}
GROUP BY ID

"""

# Exécution de la requête
df = pd.read_sql(query, conn)

# Sauvegarde dans un fichier Excel
output_file = "resultats_films.xlsx"
df.to_excel(output_file, index=False, engine="openpyxl")

st.write(f"Fichier Excel généré : {output_file}")

st.write(df.head())  # Display 5 first lines
# Fermeture de la connexion
conn.close()


#nb_lines=df.shape[0]
if df.columns.tolist() == ["line","ID","title","director","country","refyear","support","Reference","MeetingId"]:


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
        title=row["title"]

        dir_tmp=row["director"]
        country_tmp=row["country"]
        ryear=row["refyear"]
        reference=row["Reference"]
    ###############################################################################################################################



        if len(dir_tmp)>1:
            dir = [d.strip() for d in dir_tmp.split(",")]
        if len(country_tmp) >1:
            country= [cou.strip() for cou in country_tmp.split(",")]

    
        # Vérifier si les champs obligatoires sont remplis
        if not ryear:
            ryear=1950
                
                

        if reference:
            st.markdown(f"### Line n°{line_nb} <span style='color: orange;'>'{title}'</span> (Reference : {reference})", unsafe_allow_html=True)
        else:
            st.markdown(f"### Line n°{line_nb} <span style='color: orange;'>'{title}'</span> (No reference found)", unsafe_allow_html=True)
        # if not id:
        #     st.warning("If you do not provide a Coeurimages identifier, the film will not be linked to Coeurimages data.")
        res=lumatch.matching_project(title,"","",dir,country,ryear,id,token) #res est une liste de dictionnaires


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
    st.error("The excel file is not readable (pay attention to column names: line, ID, title, director, country, refyear, ...).")
                



