
from tqdm.notebook  import tqdm
from selenium import webdriver
from selenium.webdriver.common.by import By
import selenium.common.exceptions as sele_excep
from selenium.webdriver.edge.options import Options
import requests as req
import gzip as gz
import pandas as pd

tqdm.pandas()

URL_IMDB_CANNES="https://www.imdb.com/event/ev0000147/" # add year/1 at the end (ex 2023 : "https://www.imdb.com/event/ev0000147/2023/1")
URL_IMDB_BERLINALE="https://www.imdb.com/event/ev0000091/" # add year/1 at the end (ex 2020 : "https://www.imdb.com/event/ev0000091/2020/1")
URL_IMDB_GOLDEN_GLOBES="https://www.imdb.com/event/ev0000292/" # add year/1 at the end
URL_IMDB_ROTTERDAM="https://www.imdb.com/event/ev0000569/" # add year/1 at the end
URL_IMDB_OSCARS="https://www.imdb.com/event/ev0000003/" #Academy Awards, add year/1 at the end
URL_IMDB_CPH_DOX="https://www.imdb.com/event/ev0000982/" # add year/1 at the end
URL_IMDB_ANNECY="https://www.imdb.com/event/ev0000031/" # add year/1 at the end
URL_IMDB_KARLOVY_VARY="https://www.imdb.com/event/ev0000384/" # add year/1 at the end
URL_IMDB_LOCARNO="https://www.imdb.com/event/ev0000400/" # add year/1 at the end
URL_IMDB_SARAJEVO="https://www.imdb.com/event/ev0000871/" # add year/1 at the end
URL_IMDB_VENICE="https://www.imdb.com/event/ev0000681/" # add year/1 at the end
URL_IMDB_SAN_SEBASTIAN="https://www.imdb.com/event/ev0000588/" # add year/1 at the end
URL_IMDB_POFF="https://www.imdb.com/event/ev0001559/" # add year/1 at the end
URL_IMDB_EUROPEAN_FILM_AWARDS="https://www.imdb.com/event/ev0000230/" # add year/1 at the end
ALL_FESTIVALS={"annecy" : URL_IMDB_ANNECY
               ,"berlinale" : URL_IMDB_BERLINALE
               ,"cannes" : URL_IMDB_CANNES
               ,"cph_dox" : URL_IMDB_CPH_DOX
               ,"european_film_awards" : URL_IMDB_EUROPEAN_FILM_AWARDS
               ,"golden_globes" : URL_IMDB_GOLDEN_GLOBES
               ,"karlovy_vary" : URL_IMDB_KARLOVY_VARY
               ,"locarno" : URL_IMDB_LOCARNO
               ,"oscars" : URL_IMDB_OSCARS
               ,"poff" : URL_IMDB_POFF
               ,"rotterdam" : URL_IMDB_ROTTERDAM
               ,"san_sebastian" : URL_IMDB_SAN_SEBASTIAN
               ,"sarajevo" : URL_IMDB_SARAJEVO
               ,"venice" : URL_IMDB_VENICE}

class EmptyNominee(Exception):
    pass

def is_winner(nominee):
    try:
        nominee.find_element(By.CLASS_NAME, "event-widgets__winner-badge")
        return True
    except:
        return False
    
def is_name(nominee):
    return 'name' in nominee.get_attribute('href')[:25]

def has_categories(award):
    try:
        award.find_element(By.CLASS_NAME, "event-widgets__award-categories")
        return True
    except:
        return False


# TO DO:
# Fix bug when there is no primary nominee event widgets : should ignore this nominee and continue normally
def get_awards(url,progress_bar=False):
    options = Options()
    options.add_argument("--headless")
    driver = webdriver.Edge(options=options)
    driver.get(url)
    try:
        award_list=driver.find_elements(By.CLASS_NAME, "event-widgets__award")

        awards=dict()

        if progress_bar:
            loop_list=tqdm(award_list)
        else:
            loop_list=award_list

        for award in loop_list:

            award_subcategory=award.find_elements(By.CLASS_NAME, "event-widgets__award-category")

            #sometimes there are different category but it is still the same award, I test this by trying to find a subcategory award name and if it fails i merge the subcategory with the previous one
            real_award_category=[award_subcategory[0]]
            real_award_category_size=1
            for i in range(1,len(award_subcategory)):
                if len(award_subcategory[i].find_elements(By.CLASS_NAME,"event-widgets__award-category-name")) !=0 and len(award_subcategory)>1: #there is a subcategory name
                    real_award_category.append(award_subcategory[i])
                elif len(award_subcategory)==1: #if there is only one category : normal case
                    real_award_category=award_subcategory
                else:
                    if type(real_award_category[real_award_category_size-1])!=list:
                        real_award_category[real_award_category_size-1]=[real_award_category[real_award_category_size-1],award_subcategory[real_award_category_size]]
                    else:
                        real_award_category[real_award_category_size-1].append(award_subcategory[real_award_category_size])
                        real_award_category_size+=1

            # print(award.find_element(By.CLASS_NAME, "event-widgets__award-name").text) # for debugging

            for sub_award in real_award_category: # if there is no subcategory this loop will execute only one time normally
                # sub_award can be an element or a list of elements 

                if type(sub_award)!=list: #normal case
                    if len(real_award_category)>1:
                        try:
                            award_name=award.find_element(By.CLASS_NAME, "event-widgets__award-name").text+' - '+sub_award.find_element(By.CLASS_NAME,"event-widgets__award-category-name").text
                        except: # sometimes there is some categories but the first one desn't have a name as in "The Annecy cristal" here : https://www.imdb.com/event/ev0000031/2008/1
                            award_name=award.find_element(By.CLASS_NAME, "event-widgets__award-name").text
                    else:
                        award_name=award.find_element(By.CLASS_NAME, "event-widgets__award-name").text
                    nominees_list=[]
                    try :
                        for nominee in sub_award.find_elements(By.CLASS_NAME, "event-widgets__award-nomination"):
                            
                            temp_nominee_dict=dict()
                            try:
                                primary=nominee.find_element(By.CLASS_NAME, "event-widgets__primary-nominees [href]")
                            except sele_excep.NoSuchElementException as e: #there is no primary nominee it's probably because there is a bug and the film/person is empty
                                raise EmptyNominee("No element found for primary nominee : primary=nominee.find_element(By.CLASS_NAME, 'event-widgets__primary-nominees [href]')")
                            except Exception as e:
                                print(f"error URL= {url} on primary=nominee.find_element(By.CLASS_NAME, 'event-widgets__primary-nominees [href]') : {e}")
                            secondary=nominee.find_element(By.CLASS_NAME, "event-widgets__secondary-nominees") # here we don't need the [href] as it's enough to test the primary and sometimes there is only the primary

                            if is_name(primary): # tests if the primary component is a name of a person or title of a film using the provided url
                                temp_nominee_dict["director/name"]=primary.text
                                temp_nominee_dict["title"]=secondary.text
                                temp_nominee_dict["original_title"]=nominee.find_element(By.CLASS_NAME, "event-widgets__original-title--secondary").text.removesuffix(" (original title)")
                                if len(secondary.text)>0:
                                    temp_nominee_dict["imdb_id"]=nominee.find_element(By.CLASS_NAME, "event-widgets__secondary-nominees [href]").get_attribute('href').split('/')[4]
                                else:
                                    temp_nominee_dict["imdb_id"]=''
                            else:
                                temp_nominee_dict["director/name"]=secondary.text
                                temp_nominee_dict["title"]=primary.text
                                temp_nominee_dict["original_title"]=nominee.find_element(By.CLASS_NAME, "event-widgets__original-title--primary").text.removesuffix(" (original title)")
                                temp_nominee_dict["imdb_id"]=primary.get_attribute('href').split('/')[4]

                            temp_nominee_dict["winner"]=is_winner(nominee)
                            nominees_list.append(temp_nominee_dict)
                    except EmptyNominee:
                        pass
                else: # when there is multiple category for the same award 
                    # the name of the category should be in the first category element
                    award_name=award.find_element(By.CLASS_NAME, "event-widgets__award-name").text+' - '+sub_award[0].find_element(By.CLASS_NAME,"event-widgets__award-category-name").text

                    nominees_list=[]
                    for sub_sub_award in sub_award: 
                        for nominee in sub_sub_award.find_elements(By.CLASS_NAME, "event-widgets__award-nomination"):
                            
                            temp_nominee_dict=dict()
                            primary=nominee.find_element(By.CLASS_NAME, "event-widgets__primary-nominees [href]")
                            secondary=nominee.find_element(By.CLASS_NAME, "event-widgets__secondary-nominees") # here we don't need the [href] as it's enough to test the primary and sometimes there is only the primary

                            if is_name(primary): # tests if the primary component is a name of a person or title of a film using the provided url
                                temp_nominee_dict["director/name"]=primary.text
                                temp_nominee_dict["title"]=secondary.text
                                temp_nominee_dict["original_title"]=nominee.find_element(By.CLASS_NAME, "event-widgets__original-title--secondary").text.removesuffix(" (original title)")
                                if len(secondary.text)>0:
                                    temp_nominee_dict["imdb_id"]=nominee.find_element(By.CLASS_NAME, "event-widgets__secondary-nominees [href]").get_attribute('href').split('/')[4]
                                else:
                                    temp_nominee_dict["imdb_id"]=''
                            else:
                                temp_nominee_dict["director/name"]=secondary.text
                                temp_nominee_dict["title"]=primary.text
                                temp_nominee_dict["original_title"]=nominee.find_element(By.CLASS_NAME, "event-widgets__original-title--primary").text.removesuffix(" (original title)")
                                temp_nominee_dict["imdb_id"]=primary.get_attribute('href').split('/')[4]

                            temp_nominee_dict["winner"]=is_winner(nominee)
                            nominees_list.append(temp_nominee_dict)
                awards[award_name]=nominees_list

        driver.close()
        return awards
    
    except Exception as e:
        driver.close()
        print(f"error URL= {url} : {e}")


# this downloads an available downloadable file from IMDb, saves it and returns a pandas dataframe with the informations about the average rating and number of votes
def get_titles_ratings(path_to_out_file):
    
    # URL du fichier .gz que vous souhaitez télécharger
    url_fichier_gz = 'https://datasets.imdbws.com/title.ratings.tsv.gz'

    # Chemin vers le fichier .tsv que vous souhaitez créer
    fichier_tsv = path_to_out_file

    # Télécharger le fichier .gz
    response = req.get(url_fichier_gz)
    if response.status_code == 200:
        # Écrire les données dans le fichier .tsv
        with open(fichier_tsv, 'wb') as fichier_sortie:
            fichier_sortie.write(response.content)
        # print(f"Le fichier {fichier_tsv} a été téléchargé et créé avec succès !")
    else:
        return -1
        # print(f"Échec du téléchargement du fichier : {response.status_code}")

    # Ouvrir le fichier .gz en mode binaire
    with gz.open(fichier_tsv, 'rb') as fichier_compressé:
        # Lire les données du fichier compressé
        données = fichier_compressé.read()

    # Écrire les données dans le fichier .tsv
    with open(fichier_tsv, 'wb') as fichier_sortie:
        fichier_sortie.write(données)

    return pd.read_csv(path_to_out_file,sep='\t',index_col="tconst")
    # print(f"Le fichier {fichier_tsv} a été créé avec succès !")
