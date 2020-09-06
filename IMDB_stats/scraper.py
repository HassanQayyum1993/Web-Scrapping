from requests import get
from requests.exceptions import RequestException
from contextlib import closing
from bs4 import BeautifulSoup
import re
import time
import json


def get_request(url):

    with closing(get(url, stream=True)) as resp:
        if success_response(resp):
            return resp.content
        else:
            return None


def success_response(resp):

    content_type = resp.headers['Content-Type'].lower()
    return (resp.status_code == 200
            and content_type is not None
            and content_type.find('html') > -1)


def parse_html(response):
    soap_html = BeautifulSoup(response, 'html.parser')
    type(soap_html)
    return soap_html


def get_container_list_from_html(soap_html, tag, container_name):
    container_list = soap_html.find_all(tag, class_=container_name)
    "print(type(container_list))"
    return container_list


def main():
    imdb_250_url = 'https://www.imdb.com/chart/top?ref_=nv_mv_250/'
    imdb_movie_details_url = 'https://www.imdb.com/'
    imdb_250_response = get_request(imdb_250_url)
    imdb_250_soup_html = parse_html(imdb_250_response)
    "print(imdb_soap_html)"
    movie_name_container_list = get_container_list_from_html(
        imdb_250_soup_html, 'td', 'titleColumn')
    movie_dict = []
    for ind in range(len(movie_name_container_list)):
        movie_name = movie_name_container_list[ind].a.string
        print(ind.__str__() + '.' + 'Name = ' + movie_name)
        movie_title_id = movie_name_container_list[ind].a['href']
        "print(movie_title_id)"
        movie_details_response = get_request(
            imdb_movie_details_url + movie_title_id)
        movie_details_soup_html = parse_html(movie_details_response)

        movie_rating_container = movie_details_soup_html.find(
            'span', itemprop='ratingValue')
        if movie_rating_container != None:
            movie_rating_string = movie_rating_container.text
            movie_rating = float(movie_rating_string)
        else:
            movie_rating = 0

        movie_no_of_rating_container = movie_details_soup_html.find(
            'span', itemprop='ratingCount')
        if movie_no_of_rating_container != None:
            no_of_ratings_string = movie_no_of_rating_container.string
            no_of_ratings_string = re.sub("[^0-9]", "", no_of_ratings_string)
            no_of_ratings = int(no_of_ratings_string)
        else:
            no_of_ratings = 0

        movie_genre_container = movie_details_soup_html.find(
            'h4', text='Genres:')
        movie_genre_container_parent = movie_genre_container.parent
        movie_genre_container_children = movie_genre_container_parent.findChildren(
            "a", recursive=False)
        movie_genre = []
        if movie_genre_container_children != None:
            movie_genre.append(
                movie_genre_container_children[0].string.lstrip())
            for ind2 in range(1, len(movie_genre_container_children)):
                movie_genre.append(
                    movie_genre_container_children[ind2].string.lstrip())
        else:
            movie_genre = 'empty'

        movie_gross_usa_container = movie_details_soup_html.find(
            'h4', string='Gross USA:')
        if movie_gross_usa_container != None:
            movie_gross_usa_string = movie_gross_usa_container.nextSibling
            movie_gross_usa_numeric = re.sub(
                "[^0-9]", "", movie_gross_usa_string)
            movie_gross_usa_value = int(movie_gross_usa_numeric)

        else:
            movie_gross_usa_value = 0

        movie_budget_container = movie_details_soup_html.find(
            'h4', string='Budget:')
        if movie_budget_container != None:
            movie_budget_string = movie_budget_container.nextSibling
            movie_budget_numeric = re.sub("[^0-9]", "", movie_budget_string)
            movie_budget_value = int(movie_budget_numeric)
            if movie_budget_string.find("EUR") != -1:
                movie_budget_value = int(movie_budget_value*1.13)

        else:
            movie_budget_value = 0

        movie_dict.append({
            'name': movie_name,
            'numberOfRatings': no_of_ratings,
            'rating': movie_rating,
            'genre': movie_genre,
            'grossUSA': movie_gross_usa_value,
            'budget': movie_budget_value
        })

    with open('imdbstats.json', 'w+') as json_file:
        json.dump(movie_dict, json_file, indent=1)


if __name__ == "__main__":
    main()
