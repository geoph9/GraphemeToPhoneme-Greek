#!/usr/bin/env python3

import fileinput
import warnings

from g2p_greek.phoneme_conversion import convert_word
from g2p_greek.rules import single_letter_pronounciations
from g2p_greek.english_rules import english_mappings


class Dictionary(object):
    def __init__(self, path_to_lexicon, N=3):
        self.lexicon_dict = self._lexicon_lookup(path_to_lexicon, N=N)
        self.N = 3  # Hash map key length

    @staticmethod
    def _lexicon_lookup(path_to_lexicon: str, N=3):
        # Implement a hash lookup keeping N characters as the key
        # IMPORTANT: all words in the lexicon file must be unique (appear only once in the file)
        lexicon_dict: dict = {}
        for line in fileinput.input([path_to_lexicon], openhook=fileinput.hook_encoded("utf-8")):
            word = str(line.split()[0]).strip()
            phonemes = " ".join(line.split()[1:]).replace("\n", "").strip()
            # Keep N characters if word is at least of length N
            key = word if len(word) <= N else word[:N]
            if key in lexicon_dict.keys():
                lexicon_dict[key][word] = phonemes
            else:
                # Each lexicon dict value will be a dictionary with word -> phonemes
                lexicon_dict[key] = {word: phonemes}
        return lexicon_dict

    def get_word_phonemes(self, word, initial_word=None):
        if initial_word is None:
            initial_word = word
        if len(word.strip()) == 1:
            try:
                return initial_word + " " + " ".join(convert_word(single_letter_pronounciations[word])[1]) + "\n"
            except KeyError:
                try:
                    return initial_word + " " + " ".join(convert_word(english_mappings[word])[1]) + "\n"
                except KeyError:
                    warnings.warn("The single letter word {} could not be converted.".format(word), RuntimeWarning)
                    return initial_word + " \n"
        key = word[:self.N]
        if key in self.lexicon_dict.keys():
            if word in self.lexicon_dict[key].keys():
                current_phones = self.lexicon_dict[key][word].split()
            else:
                _, current_phones = convert_word(word)  # Get word and phonemes
        else:
            _, current_phones = convert_word(word)  # Get word and phonemes
        out = initial_word + " " + " ".join(current_phones) + "\n"  # append new line at the end
        return out
