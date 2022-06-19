import re
import nltk
import string
from nltk.corpus import stopwords
from nltk import ngrams
from nltk.stem.snowball import SnowballStemmer
import operator
import smart_open
import spacy
from reverse_stemmer import ReversedStemmingUtils
from common_utils import get_raw_words, get_exclussion_list, get_hotel_ids, get_facility_category
from constants import CONSTANTS
from importlib import reload

class HotelSearchUtils:
    def __init__(self, hotel_category_fname=CONSTANTS.CATEGORY_FILE_PATH, hotel_fname=CONSTANTS.MASTER_HOTEL_FILE_PATH):
        self.nlp = spacy.load('en')
        self.stop_words = set(stopwords.words('english'))
        self.all_stop_words = set(stopwords.words('english') + list(string.punctuation) + ["", "'s"])
        self.stemmer = SnowballStemmer("english")
        self.categories = self.get_concepts(hotel_category_fname)
        self.hotels, self.hotels_categories, self.hotels_raw, self.hotels_location, self.hotels_category_matches, self.hotels_raw_words, self.hotels_stem_words, self.hotels_nouns = self.read_corpus(hotel_fname)
        self.hotel_facilities_map, self.hotel_stem_facilities = self.get_facilities(CONSTANTS.HOTEL_FACILITIES_FILE_PATH)
        self.exclusion_list = get_exclussion_list()
        self.facility_category_dict, self.facility_categories = get_facility_category()

    def read_corpus(self, hotel_fname):
        hotels = dict()
        hotels_categories = dict()
        hotels_raw = dict()
        hotels_location = dict()
        hotels_category_matches = dict()
        hotels_raw_words = dict()
        hotels_stem_words = dict()
        hotels_nouns = dict()
        with smart_open.smart_open(hotel_fname, encoding="utf-8") as f:
            for i, line in enumerate(f):
                tokens = line.split('~')
                id = tokens[0].strip()
                if id != '':
                    city = ""
                    desc = ""
                    tags = ""
                    tokens_len = len(tokens)

                    if tokens_len > 3:
                        tags = tokens[3]

                    if tokens_len > 5:
                        city = tokens[5]

                    if tokens_len > 4:
                        desc = tokens[4].lower().strip()
                        hotels_raw[id] = desc
                        hotels_category_matches[id] = self.get_category_mappings(hotels_raw[id])
                        hotels_raw_words[id] = get_raw_words(desc, self.all_stop_words)
                        hotels_location[id] = city.replace('\n', '')

                    if tokens_len > 6:
                        categories = []
                        for category in tokens[6].split(';'):
                            if category.strip() != '':
                                categories.append(category.strip())

                        hotels_categories[id] = categories

                    if tokens_len > 7:
                        nouns = []
                        for noun in tokens[7].split(';'):
                            if noun.strip() != '':
                                nouns.append(noun.strip())
                        hotels_nouns[id] = nouns

                    if tokens_len > 8:
                        hotels[id] = tokens[8]
                        hotels_stem_words[id] = tokens[8].split()
                    else:
                        hotels[id] = ''
                        hotels_stem_words[id] = []

        return hotels, hotels_categories, hotels_raw, hotels_location, hotels_category_matches, hotels_raw_words, hotels_stem_words, hotels_nouns

    def get_concepts(self, fname):
        concepts = dict()
        with smart_open.smart_open(fname, encoding="iso-8859-1") as f:
            for i, line in enumerate(f):
                tokens = line.split('~')
                category = tokens[0]
                keyphrases = tokens[1].split()
                for keyphrase in keyphrases:
                    if keyphrase.endswith(','):
                        clean_keyphrase = keyphrase[:len(keyphrase) - 1].replace('_', ' ')
                    else:
                        clean_keyphrase = keyphrase.replace('_', ' ')
                    concepts[clean_keyphrase.lower()] = category
        return concepts

    def get_nouns(self, txt):
        doc = self.nlp(txt)
        tagged_txt = []
        for token in doc:
            if token.tag_.startswith('NN'):
                tagged_txt.append(self.stemmer.stem(token.text))
        return tagged_txt

    def generate_nouns_in_file(self, fname):
        with open('hotel_nouns.txt', 'a') as output_file:
            with smart_open.smart_open(fname, encoding="iso-8859-1") as f:
                for i, line in enumerate(f):
                    tokens = line.split('~')
                    id = tokens[0]
                    city = ""
                    desc = ""
                    tags = ""
                    if len(tags) > 3:
                        tags = tokens[3]
                    if len(tokens) > 5:
                        city = tokens[5]
                    if len(tokens) > 4:
                        desc = tokens[4].lower().strip()
                        nouns = self.get_nouns(desc)
                        #print("processing " + id + "\n")
                        output_file.write(
                            id + '~' + "~".join(nouns).encode('utf-8', 'ignore').decode('ascii', 'ignore') + '\n')
        output_file.close()

    def get_hotel_nouns(self, fname):
        hotels_nouns = {}
        with smart_open.smart_open(fname, encoding="iso-8859-1") as f:
            for i, line in enumerate(f):
                tokens = line.split('~')
                id = tokens[0]
                nouns = []
                for c in range(1, len(tokens)):
                    nouns.append(tokens[c])
                hotels_nouns[id] = nouns
        return hotels_nouns

    def get_grams(self, text, report_id):
        hotels_matching_stem = dict()
        hotels_category_display = dict()
        hotels_scores = dict()
        hotels_category_matches_dict = dict()
        category_tokens = self.categorize_desc_tokens(text)
        filtered_words = []
        
        for word in text.lower().split():
            if word not in self.stop_words:
                filtered_words.append(self.stemmer.stem(word))
        text_stem = self.stemmer.stem(text)
        tri_grams = list(ngrams(filtered_words, 3)) + list(ngrams(filtered_words, 4))
        tri_grams_str = []
        for tri_gram in tri_grams:
            tri_grams_str.append(' '.join(tri_gram))
        bi_grams = list(ngrams(filtered_words, 2))
        bi_grams_str = []
        for bi_gram in bi_grams:
            bi_grams_str.append(' '.join(bi_gram))
        uni_grams = list(ngrams(filtered_words, 1))
        uni_grams_str = []
        for uni_gram in uni_grams:
            uni_grams_str.append(' '.join(uni_gram))

        hotel_ids =  get_hotel_ids(report_id)


        for hotel_id in hotel_ids:

            score = 0
            hotels_category_display[hotel_id] = set()
            hotels_matching_stem[hotel_id] = set()
            for tri_gram in tri_grams_str:
                if tri_gram in self.hotels[hotel_id]:
                    phrase = self.get_match_phrase(tri_gram, self.hotels[hotel_id])
                    hotels_matching_stem[hotel_id].add(phrase)
                    score = score + 3
            for bi_gram in bi_grams_str:
                if bi_gram in self.hotels[hotel_id]:
                    phrase = self.get_match_phrase(bi_gram, self.hotels[hotel_id])
                    hotels_matching_stem[hotel_id].add(phrase)
                    score = score + 2
            for uni_gram in uni_grams_str:
                if uni_gram in self.hotels_nouns[hotel_id]:
                    phrase = self.get_match_phrase(uni_gram, self.hotels[hotel_id])
                    hotels_matching_stem[hotel_id].add(phrase)
                    score = score + 1

            for stem_facility in self.hotel_stem_facilities[hotel_id]:
                if stem_facility in text_stem.lower():
                    facility = self.hotel_facilities_map[hotel_id][stem_facility]
                    if facility != '':
                        hotels_category_display[hotel_id].add("Hotel_Facilities:" + facility)
                        score += 5


            hotels_scores[hotel_id] = score
            hotels_category_matches_dict = self.hotels_category_matches[hotel_id]
            hotels_raw_tokens = [x.strip(string.punctuation) for x in self.hotels_raw[hotel_id].lower().split()]
            hotel_facilities = [phrase.lower() for phrase in self.hotel_facilities_map[hotel_id].values()]
            for category_token in category_tokens:
                if category_token in self.hotels_categories[hotel_id]:

                    if hotels_category_matches_dict.get(category_token) is None:
                        hotel_cat_txts = []
                    else:
                        hotel_cat_txts = hotels_category_matches_dict[category_token]
                        hotels_scores[hotel_id] = hotels_scores[hotel_id] + 10
                    #hotel_cat_txts = hotels_category_matches_dict[category_token]
#                    print(hotel_cat_txts) 

                    for hotel_cat_txt in hotel_cat_txts:
                        hotels_category_display[hotel_id].add("Category: (" + category_token + ") " + hotel_cat_txt)
                        if hotel_cat_txt in hotels_raw_tokens:

                            hotels_category_display[hotel_id].add("Category: (" + category_token + ") " + hotel_cat_txt)
                        else:
                            if ' ' in hotel_cat_txt and hotel_cat_txt in self.hotels_raw[hotel_id].lower():

                                hotels_category_display[hotel_id].add(
                                    "Category: (" + category_token + ") " + hotel_cat_txt)

                if category_token in self.facility_categories:
                    facilities = self.facility_category_dict[category_token]

                    if len(set(facilities) & set(hotel_facilities)) > 0:
                        hotels_category_display[hotel_id].add("Hotel_Facility_Categories:" + category_token)
                        hotels_scores[hotel_id] = hotels_scores[hotel_id] + 5


            if text.lower() in self.hotels_raw[hotel_id].lower():
                hotels_scores[hotel_id] = hotels_scores[hotel_id] + 30
                hotels_category_display[hotel_id].add("Match:" + text)


        return hotels_category_display, hotels_scores, hotels_category_matches_dict, hotels_matching_stem


    def categorize_desc_tokens(self, desc):
        categorized_desc = desc
        max_categories = set()
        for category in self.categories.keys():
            if category in categorized_desc:
                max_categories.add(self.categories[category])
        return list(max_categories)

    def get_category_mappings(self, desc):
        categorized_desc = desc
        max_categories = set()
        category_mappings = dict()
        for category in self.categories.keys():
            if category in categorized_desc:
                is_phrase_exist = True
                if len(category.split()) == 1:
                    words = [w.lower() for w in get_raw_words(desc, self.all_stop_words)]
                    if category not in words:
                        is_phrase_exist = False

                if is_phrase_exist:
                    max_categories.add(self.categories[category])
                    if self.categories[category] not in category_mappings.keys():
                        category_mappings[self.categories[category]] = set()
                        category_mappings[self.categories[category]].add(category)
                    else:
                        category_mappings[self.categories[category]].add(category)
        return category_mappings

    def get_facilities(self, fname):
        hotel_facilities_map = {}
        hotel_stem_facilities = {}
        with smart_open.smart_open(fname, encoding="iso-8859-1") as f:
            for i, line in enumerate(f):
                tokens = [w.strip() for w in line.split('~')]
                facilities = []
                if len(tokens) > 1:
                    facilities = tokens[1:]

                if len(tokens) > 0:
                    id = tokens[0]
                    facility_dict = {}
                    stem_facilities = []
                    for facility in facilities:
                        stem_facility = self.stemmer.stem(facility).lower()
                        stem_facilities.append(stem_facility)
                        facility_dict[stem_facility] = facility
                    hotel_facilities_map[id] = facility_dict
                    hotel_stem_facilities[id] = stem_facilities

        return hotel_facilities_map, hotel_stem_facilities

    def get_match_phrase(self, match_to_text, txt):
        phrases_set = set()
        while txt.find(match_to_text) >= 0:
            phrase = self.get_token_match(match_to_text, txt)
            phrases_set.add(phrase)
            txt = txt.replace(phrase, ' ')

        phrases_list = list(phrases_set)

        if len(phrases_list) == 1:
            return phrases_list[0]

        elif len(phrases_list) > 1:
            if txt in phrases_list:
                return txt
            else:
                return phrases_list[0]
        else:
            return None

    def get_token_match(self, match_to_text, txt):
        l = len(txt)
        start_id = txt.find(match_to_text)
        end_id = start_id + len(match_to_text)
        flag = start_id
        while flag >= 0:
            if flag == 0:
                break
            elif txt[flag - 1] == '.' or txt[flag - 1] == ' ' or txt[flag - 1] == ',':
                break
            flag -= 1
        start_id = flag

        flag = end_id
        while flag < l:
            if txt[flag] == '.' or txt[flag] == ' ' or txt[flag] == ',':
                break
            flag += 1
        end_id = flag

        return txt[start_id:end_id]

    def get_top_hotels(self, text, report_id, topn=1):
        hotels_category_display, hotels_scores, hotels_category_matches_dict, hotels_matching_stem_dict = self.get_grams(
            text, report_id)

        sorted_hotels = sorted(hotels_scores.items(), key=lambda x: x[1], reverse=True)
        results = []
        for count in range(0, len(sorted_hotels)):
            item_dict = {}
            item_dict['id'] = sorted_hotels[count][0]
            item_dict['score'] = sorted_hotels[count][1]
            matching_sentences_dict = {}
            hotel_id = sorted_hotels[count][0]

            for entity in list(hotels_matching_stem_dict[hotel_id]):
                if entity.lower() not in self.exclusion_list:
                    hotels_category_display[hotel_id].add("Match_Stem: " + entity)
                    phrase, matched_sentences = ReversedStemmingUtils().get_sentences(self.hotels_raw[hotel_id],
                                                                                      entity,
                                                                                      self.hotels_stem_words[
                                                                                          hotel_id],
                                                                                      self.hotels_raw_words[
                                                                                          hotel_id],
                                                                                      self.all_stop_words)
                    if phrase is not None and phrase.lower() not in self.exclusion_list and len(
                            matched_sentences) > 0:
                        matching_sentences_dict[phrase] = matched_sentences

            item_dict['matches'] = list(hotels_category_display[sorted_hotels[count][0]])
            if len(matching_sentences_dict) > 0:
                item_dict['matching_sentences'] = matching_sentences_dict
            results.append(item_dict)

            if (len(results) == topn):
                break

        return results

