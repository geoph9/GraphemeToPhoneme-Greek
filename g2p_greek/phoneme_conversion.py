import argparse

import os
import sys
import warnings

import re
from g2p_greek.rules import *
from g2p_greek.digits_to_words import convert_numbers

try:
    from g2p_greek.english_rules import english_mappings
except ImportError:
    english_mappings = {}
    pass

from typing import Tuple


non_characters: list = ["", " ", "(", ")", ".", ",", ";", "?", "\n", "\r", "\t"]


def convert_word(word: str) -> Tuple[str, list]:
    """ Gets a word and returns the word followed by its phonemes.
        E.g. convert_word("παράδειγμα") will produce "παράδειγμα p a0 r a1 dh i0 gh m a0"

        In order to do that we need to complete the following steps in the order provided:
            1. Convert characters to its corresponding phoneme
            2. Convert diphthongs to its phonemes (same as above)
            3. Convert triphthongs to its phonemes (to avoid clashes as "άνγκρι a1 n gh r i0" instead of a1 n g r i0)
            4. Sanity check to convert special cases

        Args:
            word: A string containing one word (if there are spaces then you should handle them beforehand)
        Returns:
            word: Either the same word as the input or the transliteration of a digit (by using convert_numbers).
            current_phones: The phones that correspond to the input word.
    """
    # print("Initial word:", word)
    word = word.strip()
    if word.isdigit():
        transliterated_word = convert_numbers(word)
        # Handle numbers that end up being more than 1 words
        if len(transliterated_word.split()) > 1:
            out = ""
            for w in transliterated_word.split():
                out += " ".join(convert_word(w)[1]) + " "
            return transliterated_word, out.strip().split()
        else:
            word = transliterated_word

    # word, current_phonemes = _check_single_chars(word)
    # # Since ψ and ξ match to two phonemes we will replace them explicitly
    # new_word = re.sub("ψ", "πσ", word)
    # new_word = re.sub("ξ", "κσ", new_word)
    # # There are some letters that are matched to more than one phoneme (e.g. ψ -> p s)
    # # We need to make those separate entries for the phonemes list
    # current_phonemes = " ".join(current_phonemes).split(" ")
    # new_word, current_phonemes = _check_diphthongs(new_word, current_phonemes)
    word, current_phonemes = _check_till_dipthongs(word)
    current_phonemes = " ".join(current_phonemes).split(" ")  # For the same reason as two lines above
    current_phonemes = _sanity_check(current_phonemes)
    # print("After sanity check, final output: ", word, " ".join(current_phonemes))
    return word, current_phonemes



def _sanity_check(phonemes: list):
    # Part 1: There should be at least one intonated vowel in each word
    #         For example, the word 'τους' is written without a tone but it
    #         is implied. so, we need to convert it from 't u0 s' to 't u1 s'.
    num_of_vowel_phones = len([ph for ph in phonemes if ph in vowel_phonemes])
    if num_of_vowel_phones == 1:  # if word is τους then we need intonation at t u1 s
        new_phonemes = []
        for ph in phonemes:
            if ph in vowel_phonemes:
                new_phonemes.append(ph.replace("0", "1"))  # add intonation
            else:
                new_phonemes.append(ph)
        phonemes = new_phonemes
    # Part 2: In Greek we do not have consecutive consonant sounds (of the same consonant).
    #         For example, we can't have a1 n n a0, this will need to be converted to a1 n a0
    ph_id = 0
    new_phonemes = []
    while ph_id < len(phonemes) - 1:
        new_phonemes.append(phonemes[ph_id])
        if phonemes[ph_id] == phonemes[ph_id + 1][0]:
            ph_id += 2
        else:
            ph_id += 1
    if ph_id == len(phonemes) - 1:
        new_phonemes.append(phonemes[ph_id])
    return new_phonemes


def _get_word_couples(word):
    # Return character couples from the input word
    # e.g. from the word "hello" to ("he", "el", "ll", "lo")
    return [c + word[i+1] for i, c in enumerate(word[:-1])]


def _check_till_dipthongs(word):
    word_couples = _get_word_couples(word)
    phons = []
    counter = 0
    while counter < len(word_couples):
        if word_couples[counter] in diphthong_rules.keys():
            if len(phons) > 0: del phons[-1]
            phons.append(diphthong_rules[word_couples[counter]])
            if counter + 1 < len(word_couples):
                word_couples[counter + 1] = word_couples[counter+1][-1]  # convert 'ια' to 'α' since 'ι' is being used by the previous dipthong
        else:
            for val in word_couples[counter]:
                phons.append(character_rules[val])
            if counter + 1 < len(word_couples): 
                # in order to avoid duplicates
                if word_couples[counter+1] not in diphthong_rules.keys(): word_couples[counter+1] = word_couples[counter+1][1]
        counter += 1
    return word, phons

# def _check_triphthongs(word: str):
#     raise NotImplementedError()
#     phonemes: list = []
#     for triphthong, phoneme in triphthong_rules.items():
#         if triphthong in word.lower():
#             occurrences: list = [(a.start(), a.end()) for a in list(re.finditer(triphthong, word))]
#             for start_index, end_index in occurrences:
#                 phonemes.append()


# def _check_single_chars(word: str) -> Tuple[str, list]:
#     phonemes: list = []
#     for char in word.strip():
#         if char in non_characters:
#             continue
#         if char not in character_rules.keys():
#             raise ValueError("Character: " + char + " could not be found in the list of phonemes. It appeared in the "
#                                                     "word: " + word + ".")
#         else:
#             phonemes.append(character_rules[char])
#     return word, phonemes


# def _check_diphthongs(word: str, current_phonemes: list) -> Tuple[str, list]:
#     """
#     Take a word and the current phonemes taken from the single characters. Example input:
#         word = "γειά", current_phonemes = "gh e0 i0 a1"
#     We would like to convert the phonemes of the above into "gh i0 a1"
#     """
#     if len(word.strip()) <= 1:
#         return word, current_phonemes
#     assert len(current_phonemes) == len(word), "Number of characters does not equal to number of phonemes. In word " \
#                                                "{} current phonemes where: {}.".format(word, current_phonemes)
#     FOUND_DIPHTHONG = False
#     new_phonemes: list = []
#     for diphthong, phoneme in diphthong_rules.items():
#         if diphthong in word:
#             occurrences: list = [(a.start(), a.end() - 1) for a in list(re.finditer(diphthong, word))]
#             if len(occurrences) >= 1:
#                 FOUND_DIPHTHONG = True
#             else:
#                 continue
#             for (start_index, end_index) in occurrences:
#                 new_phonemes = []  # [""] * len(phonemes)
#                 for phon_id in range(len(current_phonemes)):
#                     if start_index <= phon_id <= end_index:
#                         new_phonemes.append(phoneme)  # we will end up wil gh i0 i0 a1
#                     else:
#                         new_phonemes.append(current_phonemes[phon_id])
#                 current_phonemes = new_phonemes
#     # If we haven't found any diphthong then ignore the replacement
#     if not FOUND_DIPHTHONG:
#         return word, current_phonemes
#     # Right now the phonemes will probably have duplicates (like in gh i0 i0 a1)
#     phonemes = [phon for i, phon in enumerate(new_phonemes[:-1]) if phon != new_phonemes[i+1]] + [new_phonemes[-1]]
#     return word, phonemes

