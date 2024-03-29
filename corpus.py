import sys
import codecs
from typing import Type
from datetime import datetime
import nltk
import numpy
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.tag import pos_tag
from nltk.chunk import conlltags2tree, tree2conlltags, ne_chunk
import statistics
import math
import re
from operator import itemgetter


class Corpus:
    name = None  # name of file and corpus
    raw = None  # output of readed file
    nltk_ = None  # nltk data
    token = None  # tokenized copy of the corpus
    sentences = None  # sentence-tokenized copy of the corpus
    pos_tag_universal = None  # pos-tagged (with universal tag) version of the corpus
    pos_tag = None  # pos-tagged version of the corpus
    n_token = None  # number of tokens
    n_sentences = None  # number of sentences

    # CONSTRUCTOR
    # Args:
    #   file_name: name of the txt file that contain the corpus
    def __init__(self, file_name):
        self.name = file_name
        temp = codecs.open(self.name, "r", "utf-8-sig")
        self.raw = temp.read().lower()
        self.nltk_ = nltk.data.load("tokenizers/punkt/english.pickle")

    # Getter and setter methods
    def get_name(self):
        return self.name

    def _set_name(self):
        raise AttributeError("Attribute can't be changed")

    def get_raw(self):
        return self.raw

    def _set_raw(self):
        raise AttributeError("Attribute can't be changed")

    def get_nltk(self):
        return self.nltk_

    def _set_nltk(self):
        raise AttributeError("Attribute can't be changed")

    def get_token(self):
        if self.token is None:
            self._set_token()
        return self.token

    def _set_token(self):
        self.token = word_tokenize(self.get_raw())

    def get_sentences(self):
        if self.sentences is None:
            self._set_sentences()
        return self.sentences

    def _set_sentences(self):
        self.sentences = sent_tokenize(self.get_raw())

    def get_pos_tag_universal(self):
        if self.pos_tag_universal is None:
            self._set_pos_tag_universal()
        return self.pos_tag_universal

    def _set_pos_tag_universal(self):
        self.pos_tag_universal = pos_tag(self.get_token(), tagset="universal")

    def get_pos_tag(self):
        if self.pos_tag is None:
            self._set_pos_tag()
        return self.pos_tag

    def _set_pos_tag(self):
        self.pos_tag = pos_tag(self.get_token())

    def get_n_sentences(self):
        return len(self.get_sentences())

    def _set_n_sentences(self):
        raise AttributeError("Attribute can't be changed")

    def get_n_token(self):
        return len(self.get_token())

    def _set_n_token(self):
        raise AttributeError("Attribute can't be changed")

    # Returns the arithmetic mean of number of tokens in the sentences of the corpus.
    def mean_sentences(self):
        temp = []
        for sentence in self.get_sentences():
            temp.append(len(word_tokenize(sentence)))
        return statistics.mean(temp)

    # Returns the arithmetic mean of number of letters in the tokens of the corpus.
    def mean_token(self):
        temp = []
        for token in self.get_token():
            temp.append(len(token))
        return statistics.mean(temp)

    # Returns the vocabulary length of the corpus (given corpus dimension)
    # Args:
    #   dimension: length of the corpus whose vocabulary is measured, when
    #              dimension is  None the method calculate vocabulary of the all corpus
    def vocabulary_length(self, dimension=None):
        if dimension is None:
            dimension = self.get_n_token()
        return len(list(dict.fromkeys(self.get_token()[:dimension])))

    # Returns an array with length of vocabulary of corpus of incremental dimension
    # ARGS:
    #   incremental: scale of incrementation, when incremental is None the default value is 1000
    def incremental_vocabulary_length(self, incremental=None):
        if incremental is None:
            incremental = 1000
        vocabulary_length = dict()
        for i in range(0, self.get_n_token(), incremental):
            vocabulary_length[i] = self.vocabulary_length(i)
        return vocabulary_length

    # Returns the hapax distribution for a portion of the corpus
    # Args:
    #   dimension: length of the corpus whose hapax distribution is measured, when dimension
    #               is None the method calculate the hapax distribution of the all corpus
    def hapax_distribution(self, dimension=None):
        if dimension is None:
            dimension = self.get_n_token()
        token_freq = dict()  # keys-> word | value -> f(word)
        output = []  # list of hapax
        for token in self.get_token()[:dimension]:  # calculating frequencies
            if token not in token_freq:
                token_freq[token] = 0
            token_freq[token] += 1
        for freq in token_freq:  # copying in the output only the hapax
            if token_freq[freq] == 1:
                output.append(freq)
        return len(output)

    # Returns an array with hapax distribution of corpus of incremental dimension
    # ARGS:
    #   incremental: scale of incrementation, when incremental is None the default value is 1000
    def incremental_hapax_distribution(self, incremental=None):
        if incremental is None:
            incremental = 1000
        hapax_distribution = dict()
        for i in range(0, self.get_n_token(), incremental):
            hapax_distribution[i] = self.hapax_distribution(i)
        return hapax_distribution

    # Returns ratio between A POS-category and B POS-category
    # ARGS:
    #   A: first POS category used to calculate the ratio
    #   B: second POS category used to calculate the ratio
    def ratio(self, a, b):
        a_count = 0
        b_count = 0
        for tag in self.get_pos_tag_universal():
            if tag[1] == a.upper():
                a_count += 1
            elif tag[1] == b.upper():
                b_count += 1
        return a_count / b_count

    # Returns an ordinated(most common to less common) list containing the tag of the pos tagged corpus
    # ARGS:
    #   dimension: length of the corpus whose most frequent POS category is measured, when dimension
    #               is None the method calculate the most frequent POS category of the all corpus
    def most_frequent_pos(self, dimension=None):
        if dimension is None:
            dimension = self.get_n_token()
        token, cat = zip(*self.get_pos_tag_universal())  # separate the POS-tag list in to 2 different lists
        temp = dict()
        for i in range(dimension):
            if cat[i] in temp.keys():
                temp[cat[i]] += 1
            else:
                temp[cat[i]] = 1
        temp = list(sorted(temp.items(), key=itemgetter(1), reverse=True))
        cat, frequency = zip(*temp)
        return cat

    # Returns an ordinated(highest to lowest) list containing conditioned probability of bigrams
    def conditioned_probability(self):
        freq_category = dict()
        freq_bigrams = dict()
        prob = dict()  # output
        pos_tag_l = self.get_pos_tag_universal()
        for i in range(len(pos_tag_l) - 1):
            if pos_tag_l[i][1] not in freq_category:
                freq_category[pos_tag_l[i][1]] = 0
            freq_category[pos_tag_l[i][1]] += 1
            if (pos_tag_l[i][1], pos_tag_l[i + 1][1]) not in freq_bigrams:
                freq_bigrams[(pos_tag_l[i][1], pos_tag_l[i + 1][1])] = 0
            freq_bigrams[(pos_tag_l[i][1], pos_tag_l[i + 1][1])] += 1
        # checking the last element of the array
        if pos_tag_l[len(pos_tag_l) - 1][1] not in freq_category:
            freq_category[pos_tag_l[len(pos_tag_l) - 1][1]] = 0
        freq_category[pos_tag_l[len(pos_tag_l) - 1][1]] += 1
        for freq in freq_bigrams:
            prob[freq] = freq_bigrams[freq] / freq_category[freq[1]]
        prob = list(sorted(prob.items(), key=itemgetter(1), reverse=True))
        # inverts element in tuples (P[Noun|Det] --> f[Det|Noun]/f[Det])
        for element in range(len(prob)):
            prob[element] = (prob[element][0][::-1], prob[element][1])
        return prob

    # Returns an ordinated(highest to lowest) list containing the local mutual information of every bigram in the corpus
    def collocations(self):
        freq_word = dict()
        freq_bigrams = dict()
        lmi = dict()  # output
        pos_tag_l = self.get_pos_tag_universal()
        for i in range(len(pos_tag_l) - 1):
            if pos_tag_l[i][0] not in freq_word:
                freq_word[pos_tag_l[i][0]] = 0
            freq_word[pos_tag_l[i][0]] += 1
            if (pos_tag_l[i][0], pos_tag_l[i + 1][0]) not in freq_bigrams:
                freq_bigrams[(pos_tag_l[i][0], pos_tag_l[i + 1][0])] = 0
            freq_bigrams[(pos_tag_l[i][0], pos_tag_l[i + 1][0])] += 1
        # checking the last element of the array
        if pos_tag_l[len(pos_tag_l) - 1][0] not in freq_word:
            freq_word[pos_tag_l[len(pos_tag_l) - 1][0]] = 0
        freq_word[pos_tag_l[len(pos_tag_l) - 1][0]] += 1
        for freq in freq_bigrams:
            # LMI(<u, v>) = f(<u, v>) * (log2((f<u, v> * N )/ (f(u) * f(v))))
            lmi[freq] = freq_bigrams[freq] * \
                     (math.log(
                         ((freq_bigrams[freq] * len(self.get_pos_tag_universal())) / (freq_word[freq[0]] * freq_word[freq[1]])),
                         2))
        lmi = list(sorted(lmi.items(), key=itemgetter(1), reverse=True))
        return lmi

    # Returns a ordered list (most frequent to less frequent) of the requested category of word and their frequencies
    # ARGS:
    #   category: the category to look for in the corpus:
    #       -PERSON: to find persons name
    #       -GPE: to find locations
    #       -ORGANIZATION: to find organizations
    #       -DATE: to find dates
    #       -TIME: to find times
    #       -MONEY: to find money elements
    #       -PERCENT: to find percent elements
    #       -FACILITY: to find facilities
    #   content: the word that the sentences must contain, when content = None the method return the
    #            sentences that contains the category of the all corpus
    def find_pos_category(self, category, content=None):
        word_list = list()  # lists of the word of the requested category
        output = dict()  # dictionary containing the frequencies of the requested word
        if content is None:
            # when the content is not specified the method analyze all the corpus
            analyzed_text = ne_chunk(self.get_pos_tag())
        else:
            # when the content is specified the method analyze just the sentence that contain the content
            list_to_string = ' '.join([str(elem) for elem in self.find_words(content)])
            analyzed_text = ne_chunk(pos_tag(word_tokenize(list_to_string)))
        for node in analyzed_text:
            if category.upper() in str(node):
                category_word = str(node).replace("/", " ").split()  # parsing the string containing the output
                temp_output_string = ""
                for i in range(1, len(category_word), 2):
                    temp_output_string += (str(category_word[i]) + " ")
                word_list.append(temp_output_string)
        for element in word_list:
            if content is not None and content not in element:
                # counting the number of time that element occour in the corpus when element and content are
                #  not the same so that you can find the number of occourence of a pos category excluding the one
                #  the is set as content to look for
                output[element] = str(self.get_raw()).count(element[:len(element) - 1])
            elif content is None:
                output[element] = str(self.get_raw()).count(element[:len(element) - 1])
        return list(sorted(output.items(), key=itemgetter(1), reverse=True))

    # Returns a list of sentences containing the parameter word
    # PARAM:
    #   word: word to be found
    def find_words(self, word):
        output = []
        for sentence in self.get_sentences():
            if str(word[:len(word) - 1]) in str(sentence):  # word[:len(word)-1] because NLTK returns name+space
                output.append(sentence)
        return output

    # Returns an ordinated (decreasing by their frequencies) lists of token of the specified grammar category and their frequencies
    # PARAM:
    #   category: the grammar category that the user is looking for
    #   content: the word that should be in the same sentence as the token of the specified grammar category,
    #            when content is None the method returns tokens of specified grammar category of the all corpus
    def find_grammar_category(self, category, content=None):
        word_list = list()  # list of the word of the requested category
        output = dict()  # dictionary containing the frequencies of the requested word
        if content is None:
            # when the content is not specified the method analyze all the corpus
            analyzed_text = self.get_pos_tag_universal()
        else:
            # when the content is specified the method analyze just the sentence that contain the content
            list_to_string = ' '.join([str(elem) for elem in self.find_words(content)])
            analyzed_text = pos_tag(word_tokenize(list_to_string), tagset="universal")
        for node in analyzed_text:
            if category.upper() in str(node):
                word_list.append(node[0])
        for element in word_list:
            if element not in output:
                output[element] = 0
            output[element] += 1
        return list(sorted(output.items(), key=itemgetter(1), reverse=True))

    # Returns a list of date time object in the format specified by the parameter
    # PARAM:
    #   format0: first element of the date
    #   format1: second element of the date
    #   format2: third element of the date
    #   content: the word that should be in the same sentence as the dates, when content = None the method return
    #            dates of the all corpus
    def find_date_format_regex(self, format0, format1, format2, content=None):
        temp_list = list()  # temporary list where the list of strings date is stored
        output = list()  # list of date
        list_date_format = {"d": r"([123456789])", "dd": r"(0[123456789]|[12]\d|3[01])",
                            "mm": r"(0[123456789]|1[012])", "m": r"([123456789])",
                            "month": r"([Jj]anuary|[Ff]ebruary|[Mm]arch|[Aa]pril|[Mm]ay|[Jj]une|[Jj]uly|[Aa]ugust|[Ss]eptember|[Oo]ctober|[Nn]ovember|[Dd]ecember)",
                            "abb_month": r"([Jj]an|[Ff]feb|[Mm]ar|[Aa]pr|[Jj]un|[Jj]ul|[Aa]ug|[Ss]ep(t)?|[Oo]ct|[Nn]ov|[Dd]ec)\.",
                            "yyyy": r"(\d\d\d\d)", "yy": r"(\d\d)",
                            "division": r"( +|/|\-|_|,| ,|, |\. )",
                            "final_division": r"( +|/|\-|_|,| ,|, |\.|$|\D)",
                            "initial_division": r"( +|/|\-|_|,| ,|, |\. |^)"}  # parts of regular expression
        to_date_format = {"d": "%d", "dd": "%d",
                          "mm": "%m", "m": "%m",
                          "month": "%B", "abb_month": "%b",
                          "yyyy": "%Y", "yy": "%y"}  # used to transform the strings into datetime objects
        if content is None:
            string_to_analyze = self.get_raw()
        else:
            string_to_analyze = ' '.join([str(elem) for elem in self.find_words(content)])
        date_list = re.findall(
            list_date_format["division"] + list_date_format[format0] + list_date_format["division"] + list_date_format[
                format1] + list_date_format["division"] + list_date_format[format2] + list_date_format[
                "final_division"],
            string_to_analyze)  # parsing with regular expressions looking for date
        # transform all date in the same format (format0-format1-format2)
        for date in date_list:
            temp = ""
            for element in date:
                if element is not "":
                    if len(element) == 1 and element.isdigit():
                        temp += "0" + element + "-"
                    elif len(element) != 1 and ("/" and "-" and "_" and "," and " ") not in element:
                        temp += element + "-"
            # Sept must be replaced with Sep because strptime can only parse sep
            temp_list.append(temp[:len(temp) - 1].replace("sept", "sep"))  # paste temp-date in the list of dates
        # Transform string into datetime object
        for date in temp_list:
            output.append(datetime.strptime(date, to_date_format[format0] + "-" + to_date_format[format1] + "-" +
                                            to_date_format[format2]))
        return output

    # Returns an ordinated (decreasing by their frequencies) lists of datetime object and their frequencies
    # PARAM:
    #   content: the word that should be in the same sentence as the dates, when content = None the method return
    #            dates of the all corpus
    def find_all_date_regex(self, content=None):
        date_list = list()  # lists of datetime object returned by find_date_format_regex()
        output = dict()  # dict containing as key the datetime object and as value the frequencies of the key
        date_format = {"d": "day", "dd": "day",
                       "m": "month", "mm": "month",
                       "month": "month", "abb_month": "month",
                       "yy": "year", "yyyy": "year"}  # possible value for find_date_format_regex
        for x in date_format:
            for y in date_format:
                for z in date_format:
                    if date_format[x] != date_format[y] and date_format[y] != date_format[z] and date_format[x] != \
                            date_format[z]:
                        date_list.extend(self.find_date_format_regex(x, y, z, content))
        for date in date_list:
            if date not in output:
                output[date] = 0
            output[date] += 1
        return list(sorted(output.items(), key=itemgetter(1), reverse=True))

    # Returns an ordinated (decreasing by their frequencies) lists of month as strings and their frequencies
    # PARAM:
    #   content: the word that should be in the same sentence as the month, when content = None the method return
    #           month of the all corpus
    def find_month_regex(self, content=None):
        output = dict()
        if content is None:
            string_to_analyze = self.get_raw()
        else:
            string_to_analyze = ' '.join([str(elem) for elem in self.find_words(content)])
        month_list = re.findall(
            r"([Jj]anuary|[Ff]ebruary|[Mm]arch|[Aa]pril|[Mm]ay|[Jj]une|[Jj]uly|[Aa]ugust|[Ss]eptember|[Oo]ctober|[Nn]ovember|[Dd]ecember)",
            string_to_analyze)  # parsing with regular expressions looking for complete months names
        month_list.extend(re.findall(
            r"([Jj]an|[Ff]feb|[Mm]ar|[Aa]pr|[Jj]un|[Jj]ul|[Aa]ug|[Ss]ep(t)?|[Oo]ct|[Nn]ov|[Dd]ec)\.",
            string_to_analyze))  # parsing with regular expressions looking for abbreviated months names
        for month in month_list:
            if month not in output:
                output[month] = 0
            output[month] += 1
        return list(sorted(output.items(), key=itemgetter(1), reverse=True))

    # Returns an ordinated (decreasing by their frequencies) lists of day of the week as strings and their frequencies
    # PARAM:
    #   content: the word that should be in the same sentence as the day of the week, when content = None
    #           the method return day of the week of the all corpus
    def find_day_week_regex(self, content=None):
        output = dict()
        if content is None:
            string_to_analyze = self.get_raw()
        else:
            string_to_analyze = ' '.join([str(elem) for elem in self.find_words(content)])
        month_list = re.findall(
            r"([Mm]onday|[Tt]uesday|[Ww]ednesday|[Ff]riday|[Ss]aturday|[Ss]unday)",
            string_to_analyze)  # parsing with regular expressions looking for complete months names
        month_list.extend(re.findall(
            r"([Mm]on|[Tt]ue|[Ww]ed|[Ff]ri|[Ss]at|[Ss]un)\.",
            string_to_analyze))  # parsing with regular expressions looking for abbreviated months names
        for month in month_list:
            if month not in output:
                output[month] = 0
            output[month] += 1
        return list(sorted(output.items(), key=itemgetter(1), reverse=True))

    # Returns a dictionary (keys: name, value: list of sentence) of sentences containing the persons name in the Corpus
    # PARAM:
    #   number: number of name to be found (from the ordinated lists of name from more to less frequent)
    #           when number is None the method return the dictionary of sentence containing every name
    def sentence_containing_name(self, number=None):
        if number is not None:
            names: list = self.find_pos_category("PERSON")[:number]
        else:
            names: list = self.find_pos_category("PERSON")
        output = dict()
        for name in names:
            if name[0] not in output:
                output[name[0]] = list()
            output[name[0]] += (self.find_words(name[0]))
        return output

    # Returns a tuple containing as first element the shortest sentence and as second element the longest sentence of
    # the corpus
    # PARAM:
    #   content: the word that the longest and shortest sentences must contain, when content = None the method return the
    #            longest and shortest sentences of the all corpus
    def min_max_sentence(self, content=None):
        if content is None:
            sentences = self.get_sentences()
        else:
            sentences = self.find_words(content)
        return min(sentences, key=len), max(sentences, key=len)

    # Returns an ordinated (more probable to less probable) list containing sentences and their markov's (order 0) probability
    # PARAM:
    #   content: the word that the sentence must contain, when None the method return the sentences of the all corpus
    #   min_length: the minimum length (in tokens) of the sentences,
    #               when None the method return the sentences of the all corpus
    #   max_length: the maximum length (in tokens) of the sentences,
    #               when None the method return the sentences of the all corpus
    def probability_markov0(self, content=None, min_length=None, max_length=None):
        freq = nltk.FreqDist(self.get_token())  # frequency of every token in the corpus
        output = dict()
        if content is None:
            sentences = self.get_sentences()
        else:
            sentences = self.find_words(content)
        for sentence in sentences:
            prob = 1.0  # initial probability
            tokens = word_tokenize(sentence)
            if (min_length <= len(tokens) <= max_length) or (min_length is None and max_length is None) or (min_length is None and len(tokens) <= max_length) or (min_length <= len(tokens) and max_length is None):
                for token in tokens:
                    prob *= (freq[token] * 1.0 / self.get_n_token() * 1.0)
                output[sentence] = prob
        return list(sorted(output.items(), key=itemgetter(1), reverse=True))
