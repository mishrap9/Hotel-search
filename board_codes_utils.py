import csv
import string

from common_utils import remove_stop_word

custom_stopwords = {'where', 'some', 'o', 'and', 'a', "won't", 'other', 'theirs', 'further', 'or', 'in', 'was', 'isn', 'each', 'we', 'ourselves', 'this', 'under', 'after', 'be', 'once', 'you', 'on', 'do', 'is', 'ma', 'very', 'can', 'just', 'then', 'such', 'here', 'ours', 'own', 'below', 'to', 'while', 'its', 'ain', 'myself', 'has', 'most', 'why', 'itself', 'are', 'out', "you've", 'more', 'an', 'same', 'of', 'between', "weren't", 'themselves', 'your', 'when', 'whom', 'her', "that'll", "you're", 'the', 'off', 'any', 'than', 'too', "isn't", 'few', 'doing', 'over', 'our', 'so', "mustn't", 'd', 'had', 'above', 'i', 'my', "hadn't", 'will', 'down', "wouldn't", 'now', 'before', 'them', 'because', 'hasn', 'there', 've', 'at', 'weren', "you'll", 'y', "needn't", 'both', 'during', "haven't", 'him', 'am', 'herself', 'that', 'until', 'she', 'they', 'm', 'how', 'having', 'haven', 'mightn', 'did', 'll', 'which', 'these', 's', 'their', "shan't", 'yourself', 'himself', 'but', 't', "you'd", 'those' 'doesn', 'from', "it's", 'by', "she's", 'into', 'if', 'were', 'his', 'it', 'as', 'won', 'what', 'been', 'against', 'mustn', 'couldn', 'through', 'yourselves', 'yours', 'he', 'again', 'hadn', 'me', 'about', 'up', 'have', "wasn't", 'who', 're', 'shan', 'wasn', 'hers', 'for', "couldn't", 'didn', 'being'}


def gen_id_boardcodes(path):
    file = open(path, "r")
    reader = csv.reader(file)
    id_dictionary = dict()
    for line in reader:
        id_boardCodes = str(line[0]).split("~")
        id = id_boardCodes[0].strip()
        boardCodes = id_boardCodes[1].split(";")
        id_dictionary[id] = boardCodes
    return id_dictionary

def get_stemmed_query(raw_text, stemmer):
    raw_words = [x.strip(string.punctuation) for x in raw_text.lower().split()]
    raw_words_without_stop_words = remove_stop_word(raw_words, custom_stopwords)
    stemmed_words = []
    for word in raw_words_without_stop_words:
        stemmed_words.append(stemmer.stem(word))
    return " ".join(stemmed_words)


def get_board_code_phrase_dict(path, stemmer):
    file = open(path, "r")
    reader = csv.reader(file)
    board_dict=dict()
    for line in reader:
        word = line[0].split("~")
        board_code = word[0].strip()
        phrase_sentences = word[1].split(";")
        stemmed_sentences=set()
        for particular_sentence in phrase_sentences:
            stemmed_words=[]
            particular_sentence_words=[x.strip(string.punctuation) for x in particular_sentence.split()]
            for words in particular_sentence_words:
                stemmed_words.append(stemmer.stem(words))
            sent = " ".join(stemmed_words)
            stemmed_sentences.add(sent)
        board_dict[board_code] = list(stemmed_sentences)
    return board_dict

def get_board_codes_from_query_text(query_text, stemmer, board_codes_phrase_dict):
    stemmed_query = get_stemmed_query(query_text, stemmer)
    board_Codes = set()
    for k in board_codes_phrase_dict.keys():
        is_added = False
        for phrase in board_codes_phrase_dict[k]:
            if phrase in stemmed_query:
                if is_valid(phrase, stemmed_query):
                    board_Codes.add(k)
                    is_added = True
            if is_added:
                break

    return list(board_Codes)


def is_valid(phrase, txt):
    phrase_len = len(phrase)
    txt_len = len(txt)
    s_index = txt.find(phrase)
    if (s_index == 0 or (s_index > 0 and txt[s_index - 1] == ' ')) and (s_index+phrase_len == txt_len or (s_index+ phrase_len < txt_len and txt[s_index + phrase_len] == ' ')):
        return True

    return False
