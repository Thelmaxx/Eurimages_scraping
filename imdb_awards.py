
from tqdm.notebook  import tqdm
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By

tqdm.pandas()

IMDB_CANNES="https://www.imdb.com/event/ev0000147/" # add at the end the year and /1 (ex 2023 : "https://www.imdb.com/event/ev0000147/2023/1")
IMDB_BERLINALE="https://www.imdb.com/event/ev0000091/" # add at the end the year and /1 (ex 2020 : "https://www.imdb.com/event/ev0000091/2020/1")

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
    
def get_awards(url):
    driver = webdriver.Edge()
    driver.get(url)
    try:
        award_list=driver.find_elements(By.CLASS_NAME, "event-widgets__award")

        awards=dict()
        for award in tqdm(award_list):

            award_subcategory=award.find_elements(By.CLASS_NAME, "event-widgets__award-category")

            for sub_award in award_subcategory: # if there is no subcategory this loop will execute only one time normally
                if len(award_subcategory)>1:
                    award_name=award.find_element(By.CLASS_NAME, "event-widgets__award-name").text+' - '+sub_award.find_element(By.CLASS_NAME,"event-widgets__award-category-name").text
                else:
                    award_name=award.find_element(By.CLASS_NAME, "event-widgets__award-name").text
                nominees_list=[]
                for nominee in sub_award.find_elements(By.CLASS_NAME, "event-widgets__award-nomination"):
                    
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
        print(f"error : {e}")

    