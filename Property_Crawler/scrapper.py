import requests
import mysql.connector
from mysql.connector import Error
from mysql.connector import errorcode
from bs4 import BeautifulSoup
import re
import json
import pprint


def insert_into_db_table(prop_dict):
    try:
        prop_loc_list = []
        loc_list = list(prop_dict.keys())
        connection = mysql.connector.connect(
            host='localhost', database='plots', user='root')
        cursor = connection.cursor()
    # connection.autocommit = false
        insert_loc_query = "insert into location (Location) value (%s) on duplicate key update refresheddate = (curdate())"
        insert_prop_query = "insert into property (LocationID, Area, Price) value (%s, %s, %s) on duplicate key update refresheddate = (curdate())"
        sel_loc_query = "select Location, ID from location"
        # print(loc_key_list)
        cursor.executemany(insert_loc_query, loc_list)
        cursor.execute(sel_loc_query)
        idloc_list = cursor.fetchall()

        for item in range(len(idloc_list)):
            if (idloc_list[item][0],) in prop_dict.keys():
                prop_list = prop_dict[(idloc_list[item][0],)]
                #print(str(prop_list) + "," + str(item))
                for item2 in range(len(prop_list)):
                    prop_loc_list.append(
                        (idloc_list[item][1], prop_list[item2][0], prop_list[item2][1]))

        cursor.executemany(insert_prop_query, prop_loc_list)

        connection.commit()

    except mysql.connector.Error as error:
        print("Failed to insert into MySQL table {}".format(error))
        connection.rollback()
        # connection.rollback()

    finally:
        if (connection.is_connected()):
            cursor.close()
            connection.close()
            print("MySQL connection is closed")


ind = 0
prop_dict = {}
props_json = []
for x in range(10):
    URL = f'https://www.zameen.com/Residential_Plots/Lahore-1-{x+1}.html'
    page = requests.get(URL)

    soup = BeautifulSoup(page.content, 'html.parser')
    props_list = []
    loc_list = []
    props_elem = soup.find_all(attrs={"role": "article"})

    for prop in props_elem:
        loc_elem = prop.find(attrs={"aria-label": "Listing location"})
        if loc_elem is None:
            loc_txt = 'empty'
        else:
            loc_txt = loc_elem.text

        price_elem = prop.find(attrs={"aria-label": "Listing price"})
        if price_elem is None:
            price = 0
        else:
            if price_elem.text.find("Crore") != -1:
                price_str = re.sub("[^0-9.]", "", price_elem.text)
                price_str = float("{:.2f}".format(float(price_str)))*100
            else:
                price_str = re.sub("[^0-9.]", "", price_elem.text)
                price = float("{:.2f}".format(float(price_str)))

        size_elem = prop.find('span', string=re.compile(r'Kanal|Marla'))
        if size_elem is None:
            size = 0
        else:
            if size_elem.text.find("Kanal") != -1:
                size_str = re.sub("[^0-9.]", "", size_elem.text)
                size = float("{:.2f}".format(float(size_str)))*20
            else:
                size_str = re.sub("[^0-9.]", "", size_elem.text)
                size = float("{:.2f}".format(float(size_str)))

        props_json.append(
            {'loc': loc_txt, 'price': price, 'size': size})

        # props_list.append((size, price))
        loc_tuple = (loc_txt,)
        # loc_list.append(loc_tuple)
        # insert_into_db_table(loc_tuple, size, price)
        prop_dict.setdefault((loc_txt,), []).append([size, price])
        # print(props_json)

insert_into_db_table(prop_dict)
json_object = json.dumps(props_json, indent=4)
# print(json_object)
# Writing to sample.json
with open("sample.json", "w") as outfile:
    outfile.write(json_object)
print("written into sample.json")
