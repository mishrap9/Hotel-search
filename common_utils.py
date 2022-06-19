import nltk
import requests
import json
import string

from constants import CONSTANTS

def get_exclussion_list(fname='/mnt/exclusions.csv'):
    exclusion_list = set()
    with open(fname, 'r') as file:
        for l in file:
            exclusion_list.add(l.strip())

    return list(exclusion_list)

def remove_stop_word(words, stop_words):
        return [w for w in words if not w in stop_words]

def get_raw_words(raw_text, stop_words):
    raw_text = raw_text.replace('*', ' ')
    raw_text = raw_text.replace('+', ' ')
    raw_text = raw_text.replace('?', ' ')
    raw_words = [x.strip(string.punctuation) for x in raw_text.split()]
    raw_words_with_out_stop_words = remove_stop_word(raw_words, stop_words)
    return raw_words_with_out_stop_words

def get_hotel_ids(report_id):

    url = "https://sandman.thewaylo.com/api/rates/report/" + report_id 

    payload = '{"key": "_roamamore_waylo_","notCombined": true}'
    headers = {'Content-Type': "application/json"}

    response = requests.request("POST", url, data=payload, headers=headers)
    json_txt = json.loads(response.text)
    hotel_ids = []
    if json_txt["success"]:
        json_hotels =  json_txt["report"]["hotels"]
        for item in json_hotels:
            hotel_ids.append(item['_id'].strip())

    return hotel_ids

def get_facility_category( fname = CONSTANTS.FACILITES_FILE_PATH ):
    facility_category_dict = {}
    facility_categories = set()
    with open(fname, 'r') as file:
        for line in file:
            tokens = [phrase.strip() for phrase in line.split('~')]
            if len(tokens) == 2:
                facility = tokens[0]
                category = tokens[1]
                if category != '':
                    facility_categories.add(category)
                    if category in facility_category_dict.keys():
                        facility_category_dict[category].add(facility)
                    else:
                        facility_category_dict[category] = {facility}

    return facility_category_dict, list(facility_categories)
