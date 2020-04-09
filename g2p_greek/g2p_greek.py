#!/usr/bin/env python3

# MIT License
#
# Copyright (c) 2019 geoph9
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
    Description: There are 3 parsers and all of them are mixed into a single super parser. This script contains two
                 modes.
                 1. In the first one you can pass a text file containing all of the words that appear in your
                    dataset (e.g. in the kaldi 'text' file). In this case, you need to provide the path to the words
                    file and the path to the lexicon file based on which the word phonemes will be computer. I.e.
                    for each word, if the word exists in the lexicon (e.g. in the cmu sphinx lexicon) then the
                    phonemes will be calculated from that. Otherwise, the phonemes will be calculated from the
                    algorithm above.

                 2. In the second mode you can pass a path to a text file that contains only the unknown words ->
                    a.k.a the words that do not exist in the original lexicon. The algorithm above will compute
                    the phonemes of the words based on the rules explained in the comments.
                    This mode may also come handy if you don't want to loose time loading the original lexicon
                    everytime you want to compute the phonemes of a word. Though, note that the phonemes are not
                    always the same as the ones in the el-gr.dic lexicon provided by cmu_sphinx. This is because
                    some words in the lexicon contain consecutive vowels such as αααα but the algorithm above
                    replaces them with single vowels (so αααα will be replaced with α). This may make sense for
                    some words but it may cause problems with others so we advice using this mode only when you
                    don't have words with consecutive consonants.

                For testing purposes you may also use the -t flag (--test-word) followed by a word and check its
                output.

                IMPORTANT: The phoneme structure should be the same as the one in the greek lexicon of cmu sphinx.
                           Check the rules.py to view all of the available phonemes.
"""

import argparse

import os
import fileinput
import sys

import re
from g2p_greek.rules import *
from g2p_greek.utils import process_word, _check_dir, InvalidPathError, handle_commas
from g2p_greek.digits_to_words import convert_numbers

try:
    from g2p_greek.english_rules import english_mappings
except ImportError:
    english_mappings = {}
    pass

from typing import Tuple

non_characters: list = ["", " ", "(", ")", ".", ",", ";", "?", "\n", "\r", "\t"]


def _check_triphthongs(word: str):
    raise NotImplementedError()
    phonemes: list = []
    for triphthong, phoneme in triphthong_rules.items():
        if triphthong in word.lower():
            occurrences: list = [(a.start(), a.end()) for a in list(re.finditer(triphthong, word))]
            for start_index, end_index in occurrences:
                phonemes.append()


def _check_single_chars(word: str) -> Tuple[str, list]:
    phonemes: list = []
    for char in word.strip():
        if char in non_characters:
            continue
        if char not in character_rules.keys():
            raise ValueError("Character: " + char + " could not be found in the list of phonemes. It appeared in the "
                                                    "word: " + word + ".")
        else:
            phonemes.append(character_rules[char])
    return word, phonemes


def _check_diphthongs(word: str, current_phonemes: list) -> Tuple[str, list]:
    """
    Take a word and the current phonemes taken from the single characters. Example input:
        word = "γειά", current_phonemes = "gh e0 i0 a1"
    We would like to convert the phonemes of the above into "gh i0 a1"
    """
    if len(word.strip()) <= 1:
        return word, current_phonemes
    assert len(current_phonemes) == len(word), "Number of characters does not equal to number of phonemes."
    FOUND_DIPHTHONG = False
    new_phonemes: list = []
    for diphthong, phoneme in diphthong_rules.items():
        if diphthong in word:
            occurrences: list = [(a.start(), a.end() - 1) for a in list(re.finditer(diphthong, word))]
            if len(occurrences) >= 1:
                FOUND_DIPHTHONG = True
            else:
                continue
            for (start_index, end_index) in occurrences:
                new_phonemes = []  # [""] * len(phonemes)
                for phon_id in range(len(current_phonemes)):
                    if start_index <= phon_id <= end_index:
                        new_phonemes.append(phoneme)  # we will end up wil gh i0 i0 a1
                    else:
                        new_phonemes.append(current_phonemes[phon_id])
                current_phonemes = new_phonemes
    # If we haven't found any diphthong then ignore the replacement
    if not FOUND_DIPHTHONG:
        return word, current_phonemes
    # Right now the phonemes will probably have duplicates (like in gh i0 i0 a1)
    phonemes = []
    ph_index = 0
    # The warning below is not an issue because if there are no diphthongs then FOUND_DIPHTHONG will be False and
    # so we will return earlier
    assert new_phonemes is not None, "New phonemes should contain the phoneme replacements if we got to this point."
    while ph_index < len(new_phonemes) - 1:
        if new_phonemes[ph_index] == new_phonemes[ph_index + 1]:
            phonemes.append(new_phonemes[ph_index])
            ph_index += 2
        else:
            phonemes.append(new_phonemes[ph_index])
            # phonemes.append(new_phonemes[ph_index+1])
            ph_index += 1
    if ph_index == len(new_phonemes) - 1:
        phonemes.append(new_phonemes[-1])  # add the last phoneme
    else:  # The last phoneme should have already been added from the last iteration (and ph_index would be == len)
        pass
    return word, phonemes


def _sanity_check(phonemes: list):
    # Part 1: There should be at least one intonated vowel in each word
    #         For example, the word 'τους' is written without a tone but it
    #         is implied so we need to convert it from 't u0 s' to 't u1 s'.
    num_of_vowel_phones = len([ph for ph in phonemes if ph in vowel_phonemes])
    if num_of_vowel_phones == 1:  # if word is τους then we need intonation at t u1 s
        new_phonemes = []
        for ph in phonemes:
            if ph in vowel_phonemes:
                new_phonemes.append(ph.replace("0", "1"))  # add intonation
            else:
                new_phonemes.append(ph)
        phonemes = new_phonemes
    # Part 2: In Greek we do not have consecutive consonant sounds.
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


def preprocess_and_convert_nums(word):
    word = handle_commas(word)
    # ----- BASIC PROCESSING -----
    word = process_word(word)
    # ----- REMOVE CERTAIN PUNCTUATION AND CONVERT NUMBERS TO WORDS -----
    new_word = ""
    for sub_word in word.split():
        # Split words into words and digits (numbers). E.g. είναι2 -> είναι 2
        match = re.match(r"([a-zα-ω]+)([0-9]+)", sub_word, re.I)
        if match:
            items = match.groups()
        else:
            items = [sub_word]
        for item in items:
            if item[0].isdigit() and \
                    (item.endswith("ο") or
                     item.endswith("η") or
                     item.endswith("α")):
                digit = ""
                for l in word:
                    if l.isdigit():
                        digit += l
                new_word += convert_numbers(digit) + "τ" + item[-1] + " "  # convert 10ο του δέκατο
                pass
            elif item.isdigit():
                new_word += convert_numbers(item) + " "
            else:
                for char in item:
                    if char.isdigit():
                        print("Found a digit inside a text: {}. We will ignore it and continue.".format(item))
                        continue
                    new_word += char
                new_word += " "
    new_word = re.sub(r"\s+", " ", new_word)
    return new_word


def convert_word(word: str) -> Tuple[str, list]:
    """
    Gets a word and returns the word followed by its phonemes.
    E.g. convert_word("παράδειγμα") will produce "παράδειγμα p a0 r a1 dh i0 gh m a0"

    In order to do that we need to complete the following steps in the order provided:
        1. Convert characters to its corresponding phoneme
        2. Convert diphthongs to its phonemes (same as above)
        3. Convert triphthongs to its phonemes (to avoid clashes as "άνγκρι a1 n gh r i0" instead of a1 n g r i0)
        4. Sanity check to convert special cases
    """
    # print("Initial word:", word)
    if word.strip().isdigit():
        word = convert_numbers(word)
    word, current_phonemes = _check_single_chars(word)
    # Since ψ and ξ match to two phonemes we will replace them explicitely
    new_word = re.sub("ψ", "πσ", word)
    new_word = re.sub("ξ", "κσ", new_word)
    # There are some letters that are matched to more than one phoneme (e.g. ψ -> p s)
    # We need to make those separate entries for the phonemes list
    current_phonemes = " ".join(current_phonemes).split(" ")
    new_word, current_phonemes = _check_diphthongs(new_word, current_phonemes)
    current_phonemes = " ".join(current_phonemes).split(" ")  # For the same reason as two lines above
    current_phonemes = _sanity_check(current_phonemes)
    # print("After sanity check, final output: ", word, " ".join(current_phonemes))
    return word, current_phonemes


def convert_file(path_to_file: str, out_path: str, check_dirs: bool = True):
    """ Finds the phonemes of a list of unknown words from a file in this format:
            word1
            word2
            ...
        Saves a new file in the following format:
            word1 phone1 phone2 ... phoneN
            word2 phone1 phone2 ... phoneN
        Args:
            path_to_file: A valid path to a file containing only words separated by a new line.
            out_path: A valid path to where the output lexicon will be saved.
            check_dirs: If true then it will check if the directories/paths provided exist.
        Raises:
            FileNotFoundError: If the paths provided are not valid.
    """
    if check_dirs:
        out_path = _check_dir(path_to_file=path_to_file, out_path=out_path)
    # Read input file
    with open(path_to_file, "r", encoding="utf-8") as fr:
        lines = fr.readlines()
        out_lines: list = []
        for initial_word in lines:
            word = str(initial_word.split()[0]).strip()
            word = preprocess_and_convert_nums(word)
            # The processing may have created more than one words (e.g. 102.4 -> εκατό δύο κόμμα τέσσερα)
            for sub_word in word.split():
                sub_word = str(sub_word.split()[0]).strip()
                sub_word, current_phones = convert_word(sub_word)  # Get word and phonemes
                out_lines.append(sub_word + " " + " ".join(current_phones) + "\n")  # append new line at the end
    with open(out_path, "w", encoding="utf-8") as fw:
        fw.writelines(out_lines)


def _lexicon_lookup(path_to_lexicon: str, N=3):
    # Implement a hash lookup keeping N characters as the key
    # IMPORTANT: all words in the lexicon file must be unique (appear only once in the file)
    lexicon_dict: dict = {}
    for line in fileinput.input([path_to_lexicon], openhook=fileinput.hook_encoded("utf-8")):
        word = str(line.split()[0]).strip()
        phonemes = " ".join(line.split()[1:]).replace("\n", "").strip()
        k = N if len(word) < N else len(word)  # Keep N characters if word is at least of length N
        key = word[:k]
        word_to_phoneme = {word: phonemes}  # Each lexicon dict value will be a dictionary with word -> phonemes
        if key in lexicon_dict.keys():
            lexicon_dict[key].append(word_to_phoneme)
        else:
            lexicon_dict[key] = word_to_phoneme
    return lexicon_dict


def convert_from_lexicon(path_to_words_txt: str, path_to_lexicon: str, out_path: str,
                         check_dirs: bool = True, is_shell_command: bool = False):
    if check_dirs:
        out_path = _check_dir(path_to_file=path_to_words_txt, out_path=out_path, path_to_lexicon=path_to_lexicon)
    # Get lexicon hash map
    N = 3
    # Lexicon dictionary will be of the form:
    #   { "αυτ": {"αυτός": "a0 f t o1 s", "αυτοί": "a0 f t i1", ...}, ... }
    lexicon_dict = _lexicon_lookup(path_to_lexicon, N=N)  # hash key length
    # Get words to transcribe
    with open(path_to_words_txt, "r", encoding="utf-8") as fr:
        lines = fr.readlines()
        out_lines: list = []
        for initial_word in lines:
            if initial_word.replace("\n", "").strip() == "":
                continue
            word = str(initial_word.split()[0]).strip()
            word = preprocess_and_convert_nums(word)
            if english_mappings != {}:
                for letter in set(word):
                    if letter in english_mappings.keys():
                        word = re.sub(letter, english_mappings[letter], word)
            # The processing may have created more than one words (e.g. 102.4 -> εκατό δύο κόμμα τέσσερα)
            for sub_word in word.split():
                key = sub_word[:N]
                # print(sub_word)
                if key in lexicon_dict.keys():
                    if sub_word in lexicon_dict[key].keys():
                        out_lines.append(sub_word + " " + lexicon_dict[key][sub_word] + "\n")
                    else:
                        sub_word, current_phones = convert_word(sub_word)  # Get word and phonemes
                        out_lines.append(sub_word + " " + " ".join(current_phones) + "\n")  # append new line at the end
                else:
                    sub_word, current_phones = convert_word(sub_word)  # Get word and phonemes
                    out_lines.append(sub_word + " " + " ".join(current_phones) + "\n")  # append new line at the end

    if not is_shell_command:
        # Write the new lines
        with open(os.path.abspath(out_path), "w", encoding="utf-8") as fw:
            for line in out_lines:
                fw.write(line)
    return out_lines


def main():
    """ If you have a list of words and you don't know if the words exists in the lexicon file or not then use the
        following.
        Usage: python g2p_greek.py --path-to-words-txt /home/user/data/all_words.txt \
                                   --path-to-lexicon /home/user/data/lexicon/el-gr.dic \
                                   --out-path /home/user/project/output_words.txt

        If you have a list of words and you are sure that these don't exist in the lexicon file then use this instead:
        Usage: python g2p_greek.py --path-to-unknown-words /home/user/data/non_lexicon_words.txt \
                                   --out-path /home/user/project/output_words.txt

        The latter is NOT recommended and you should do this only if you don't want to use the lexicon since it can
        be time consuming because we are loading the whole lexicon into the memory.
    """
    general_parser = argparse.ArgumentParser(
        description="For testing purposes you may use the --test-word argument followed by a single of words.",
        add_help=False
    )
    general_parser.add_argument("-o", "--out-path", required=False, default="../data/el-gr.dic",
                                # action=InvalidPathError,
                                help="Output path for the new lexicon (containing words and phonemes).")
    general_parser.add_argument("-t", "--test-word", required=False, default="",
                                help="A word (or sequence of words to be used for testing).")
    general_parser.add_argument("-sh", '--shell-command', action='store_true', dest='is_shell_command',
                                help='If true then we assume that you are calling this script from a shell command '
                                     '(i.e. a bash script). In this case, the output will be returned and printed '
                                     'in the console so that you can redirect it to where you wish. If this is provided'
                                     ' the out-path argument does not matter since the output file will be defined in '
                                     'the bash script')
    general_parser.set_defaults(is_shell_command=False)
    full_words_parser = argparse.ArgumentParser(
        description="Provide a words.txt file in kaldi format, meaning just a text file containing different "
                    "words in each line. The output will be a new lexicon file containing all of the words "
                    "followed by their phonemes. For each word, if it exists in the original cmu_sphinx lexicon then "
                    "the phonemes will be the same as there. Otherwise, the phonemes will be calculated from this "
                    "script."
                    "\nE.g. python g2p_greek.py --path-to-words-txt /home/user/words.txt"
                    "                           --path-to-lexicon /home/user/cmu_sphinx/el-gr.dic"
                    "                           --out-path /home/user/new_lexicon.dic",
        add_help=False
    )
    full_words_parser.add_argument("-w", "--path-to-words-txt", required=False, default=".", action=InvalidPathError,
                                   help="Path to the words.txt file (or any other name) that contains all of the words"
                                        "that appear in our data (e.g. in the kaldi text file).")
    full_words_parser.add_argument("-l", "--path-to-lexicon", required=False, default="../data/el-gr.dic",
                                   action=InvalidPathError,
                                   help="Path to the lexicon containing the already known phonemes of all words "
                                        "that appear in the words.txt file above.")
    unknown_words_parser = argparse.ArgumentParser(
        description="Provide a text file with unknown words (words not in lexicon) separated by new lines. There should"
                    "be as many lines as the number of words for which you want to produce the phonemes."
                    "The output will be a text file containing the words followed by their phonemes. See example below."
                    "\nE.g. python g2p_greek.py --path-to-unknown-words /home/user/unknown_words.txt "
                    "                               --out-path /home/user/new_lexicon.dic",
        add_help=False
    )
    unknown_words_parser.add_argument("-u", "--path-to-unknown-words", required=False, default=".",
                                      action=InvalidPathError,
                                      help="Path to a text file containing words in each line.")
    # a super parser for sanity checks
    super_parser = argparse.ArgumentParser(
        parents=[general_parser, full_words_parser, unknown_words_parser])
    super_parser.parse_args()
    # Parse individual arguments
    general_args, _ = general_parser.parse_known_args()
    full_words_args, _ = full_words_parser.parse_known_args()
    unknown_words_args, _ = unknown_words_parser.parse_known_args()

    # ----------------------- CONVERT TEST WORD -----------------------------
    # If there is a test word then calculate its phonemes and exit
    if general_args.test_word != "":
        word = general_args.test_word
        print("Initial word:", word)
        word = preprocess_and_convert_nums(word)
        print("Processed word:", word)
        for sub_word in word.split():
            convert_word(sub_word)
        sys.exit(0)

    # --------------------------- USE LEXICON (RECOMMENDED) -----------------------------------
    # mode 1: Using the cmu lexicon
    lex_path = full_words_args.path_to_lexicon
    if full_words_args.path_to_words_txt != "." and os.path.exists(lex_path):
        out = convert_from_lexicon(full_words_args.path_to_words_txt, lex_path, general_args.out_path, check_dirs=True)
        if general_args.is_shell_command:
            print("".join(out))
        # sys.exit(0)
    else:
        print("Could not located the lexicon path:", lex_path, ". We are proceeding to use this algorithm for "
                                                               "all conversions.")

    # ---------------------------------- USE OUR ALGORITHM ---------------------------------
    # mode 2: Do not use the lexicon
    if unknown_words_args.path_to_unknown_words != ".":
        convert_file(path_to_file=unknown_words_args.path_to_unknown_words, out_path=general_args.out_path,
                     check_dirs=True)
        sys.exit(0)


if __name__ == '__main__':
    main()
