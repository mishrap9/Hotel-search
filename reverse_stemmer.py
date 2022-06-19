import re
import nltk
import string
from nltk.corpus import stopwords

from common_utils import remove_stop_word

class ReversedStemmingUtils:

    def generate_regex(self, word_list):
        pattern = ".*?".join(word_list)
        pattern.replace('.', '\.')
        pattern.replace('(', '\(')
        pattern.replace(')', '\)')
        return r'(' + pattern + ')'

    def get_patterns(self, regex, raw_text):
        return re.findall(regex, raw_text)

    def get_text(self, word_list, txt):
        tmp_txt = txt
        index = 0
        for word in reversed(word_list):
            index = txt.rfind(word)
            tmp_txt = tmp_txt[:index]

        return txt[index:]

    def get_filtered_result(self, word_list, raw_text, stop_words):
        word_list_len = len(word_list)
        filtered_result = []
        groups = self.get_patterns(self.generate_regex(word_list), raw_text)
        for group in groups:

            txt = self.get_text(word_list, group)
            words = nltk.word_tokenize(txt)
            words_with_out_stop_words = remove_stop_word(words, stop_words)
            if words_with_out_stop_words == word_list:
                filtered_result.append(txt)

        return filtered_result

    def write_on_file(self, stem_txt, raw_txt, search_text, fname):
        with open(fname, "a") as file:
            file.write("stem_txt: ~ " + stem_txt + "\n\n")
            file.write("raw_txt: ~ " + raw_txt + "\n\n")
            file.write("search_text: ~ " + search_text + "\n\n")


    def get_original_terms(self, raw_text, search_text, stem_words, raw_words, stop_words):
        search_words = nltk.word_tokenize(search_text)
        search_words_len = len(search_words)
        stem_words_len = len(stem_words)
        original_text_list = []
        if search_words_len > 0:
            i = 0
            j = 1
            while i < stem_words_len:
                if stem_words[i] == search_words[0]:
                    flag = i
                    i += 1
                    while i < stem_words_len and j < search_words_len and stem_words[i] == search_words[j]:
                        i += 1
                        j += 1
                    if i <= stem_words_len and j == search_words_len:
                        word_list = raw_words[flag:i]
                        original_text_list += self.get_filtered_result(word_list, raw_text, stop_words)

                    j = 1
                else:
                    i += 1

        return list(set(original_text_list))

    def get_sentences(self, raw_text, search_text, stem_words, raw_words, stop_words):
        matched_sentences = set()
        sentences = nltk.sent_tokenize(raw_text)
        phrases = self.get_original_terms(raw_text, search_text, stem_words, raw_words, stop_words)
        if len(phrases) > 0 and phrases[0] != '':
            for sentence in sentences:
                if phrases[0] in sentence:
                    matched_sentences.add(sentence)

            return phrases[0], list(matched_sentences)

        return None, list(matched_sentences)

