import requests as req
from bs4 import BeautifulSoup
import json

from selenium import webdriver
from selenium.webdriver.common.by import By
import selenium.common.exceptions as sele_excep
from selenium.webdriver.edge.options import Options

def from_imdb_to_letterboxd(imdb_id):

    
    options = Options()
    options.add_argument("--headless")
    driver = webdriver.Edge(options=options)
    driver.get(f"https://letterboxd.com/search/{imdb_id}/")

    good_link=''
    found_flag=True
    c=0
    link_list=driver.find_elements(By.TAG_NAME, "a")
    while found_flag and c<len(link_list) :
        l=link_list[c].get_attribute('href')
        link_spl=l.split("/")
        if len(link_spl)==6 and found_flag:
            if link_spl[3]=='film':
                good_link=l
                found_flag=False
        c+=1

    #old method that worked before they added javascript to the website
    # rech=req.get(f"https://letterboxd.com/search/{imdb_id}/")
    # soup = BeautifulSoup(rech.text, 'html.parser')
    # good_link=''
    # found_flag=True
    # for link in soup.find_all('a'):
    #     l=link.get('href')
    #     link_spl=l.split("/")
    #     if len(link_spl)==4 and found_flag:
    #         if link_spl[1]=='film':
    #             good_link='https://letterboxd.com'+l
    #             found_flag=False

    return good_link

def rating(imdb_id):
    url=from_imdb_to_letterboxd(imdb_id)
    if type(url)!=str:
        return "can't find the movie"
    elif len(url)<25:
        return "can't find the movie"

    movie=req.get(url)

    # Parse the HTML content
    soup = BeautifulSoup(movie.text, 'html.parser')

    # Find the <script> tag with type "application/ld+json"
    script_tag = soup.find('script', type='application/ld+json')

    # Extract the JSON content
    json_content = script_tag.string.strip()

    # Remove the CDATA markers if present
    json_content = json_content.replace('/* <![CDATA[ */', '').replace('/* ]]> */', '').strip()

    # Parse the JSON content
    data = json.loads(json_content)

    # Extract the movie rating and rating count
    try:
        rating_value = data['aggregateRating']['ratingValue']
        rating_count = data['aggregateRating']['ratingCount']
        return rating_value,rating_count
    except KeyError:
        return 'no data'
    except Exception as e:
        return e
    # print(f"Rating Value: {rating_value}")
    # print(f"Rating Count: {rating_count}")
