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
import sys
import warnings

import re
from g2p_greek.rules import *
from g2p_greek.utils import process_word, _check_dir, InvalidPathError, handle_commas, handle_hours
from g2p_greek.digits_to_words import convert_numbers

from g2p_greek.dictionary import Dictionary
from g2p_greek.phoneme_conversion import convert_word

try:
    from g2p_greek.english_rules import english_mappings
except ImportError:
    english_mappings = {}
    pass


def basic_preprocessing(word: str):
    """ Basic preprocessing. Here we assume that the input (word) is a
        single word and does not contain any spaces in it. This is normal
        since, supposedly, the input is each line in a words.txt file
        (and each line is a single word by default).
        Note that this function does not convert numbers to words.
        Args:
            word: A single word.
        Returns:
            The processed outcome of the word. May be more than one words.
            For example, if the input is "10,9" then is will be converted to
            "10 κόμμα 9" (decimal handling).
            Note: The output word is always in lowercase.
    """
    word = re.sub(r"\s\t", "\t", word)
    word = handle_commas(word.lower()).strip()
    word = handle_hours(word)
    # ----- BASIC PROCESSING -----
    word = process_word(word, to_lower=False, remove_unknown_chars=True)
    # ----- REMOVE CERTAIN PUNCTUATION AND CONVERT NUMBERS TO WORDS -----
    new_word = ""
    for sub_word in word.split():
        if sub_word.strip() == "":
            continue
        # Split words into words and digits (numbers). E.g. είναι2 -> είναι 2
        words = re.split(r"(\d+)", sub_word)  # may have spaces
        words = [w for w in words if w.strip() != ""]  # remove spaces from list
        # match = re.match(r"([a-zα-ωά-ώϊΐϋΰ]+)([0-9]+)*", sub_word, re.I)
        # if match:
        #     words = match.groups()
        # else:
        #     words = [sub_word]
        for w in words:
            if w[0].isdigit() and \
                    (w.endswith("ο") or
                     w.endswith("η") or
                     w.endswith("α")):
                # Case 1: If we have words like 10ο
                digit = ""
                for l in word:
                    if l.isdigit():
                        digit += l
                new_word += convert_numbers(digit) + "τ" + w[-1] + " "  # convert 10ο to δέκατο
                pass
            elif w[0].isdigit() and (w.endswith("ος") or w.endswith("ες")):
                digit = ""
                for l in word:
                    if l.isdigit():
                        digit += l
                new_word += convert_numbers(digit) + "τ" + w[-2] + w[-1] + " "  # convert 10ος to δεκατος
            else:
                new_word += w + " "
            # elif w.isdigit():
            #     # Case 2: If the whole word is a digit then just convert it
            #     new_word += convert_numbers(w) + " "
            # else:
            #     # Case 3: Check if there are any digits left. Otherwise just leave the same word.
            #     for char in w:
            #         if char.isdigit():
            #             print("Found a digit inside a text: {}. We will ignore it and continue.".format(w))
            #             continue
            #         new_word += char
            #     new_word += " "
    new_word = re.sub(r"\s+", " ", new_word).strip()
    return new_word


def _number_to_word(number: str) -> str:
    """
        Args:
            number: A string that should match to a number.
        Returns:
            the corresponding word.
        Raises:
            ValueError if the argument is not a digit.
    """
    if not number.isdigit():
        raise ValueError("Not a number: {}.".format(number))
    return convert_numbers(number)


def convert_file(path_to_file: str, out_path: str,
                 check_dirs: bool = True,
                 use_numbers: bool = False):
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
            use_numbers: If false then the new lexicon will not contain numbers
                         but only their transliteration (the word).
        Raises:
            FileNotFoundError: If the paths provided are not valid.
    """
    if check_dirs:
        out_path = _check_dir(path_to_file=path_to_file, out_path=out_path)
    # Read input file
    with open(path_to_file, "r", encoding="utf-8") as fr:
        lines = fr.readlines()
        out_lines: list = []
        for initial_line in lines:
            words = str(initial_line.split()[0]).strip()
            # The processing may have created more than one words (e.g. 102.4 -> εκατό δύο κόμμα τέσσερα)
            for word in words.split():
                word_complex = basic_preprocessing(word)
                for initial_word in word_complex.split():
                    initial_word = initial_word.strip()  # e.g. word is "10"
                    if initial_word.isdigit():
                        if not use_numbers:  # if we don't want numbers then convert 10 to δεκα
                            initial_word = _number_to_word(initial_word)
                        else:
                            # If the number has more than 3 digits (e.g. 111) then convert
                            # the number to a word since that is more than 2 syllables.
                            if len(initial_word) > 2 and len(set(initial_word)) > 1:
                                initial_word = _number_to_word(initial_word)
                    # Get the phonemes for 10 (or δεκα)
                    _, current_phones = convert_word(initial_word)  # Get word and phonemes
                    # If use_numbers is true then write "10 dh e1 k a0"
                    # else write "δεκα dh e1 k a0"
                    out_lines.append(initial_word + " " + " ".join(current_phones) + "\n")  # append new line at the end
    with open(out_path, "w", encoding="utf-8") as fw:
        fw.writelines(out_lines)


def convert_from_lexicon(path_to_words_txt: str, path_to_lexicon: str, out_path: str,
                         check_dirs: bool = True, use_numbers: bool = False,
                         is_shell_command: bool = False):
    """
        Args:
            path_to_words_txt: The path to the words.txt file which should contain
                               one word per line.
            path_to_lexicon: The path to the lexicon which should contain some previous
                             knowledge on the phonemes of certain words. If available,
                             you should provide the CMU Greek dictionary (el-gr.dic).
            out_path: The path to where the lexicon output will be saved.
            check_dirs: If True then we are going to make sure that the files above exist.
                        (Just leave it to True.)
            use_numbers: If False then all numbers will be converted to words before writing
                         them to the lexicon. Otherwise, the lexicon will contain the numbers.
                         E.g. If True then the word 10 will be written as "10 dh e1 k a0"
                              If False then the word 10 will be written as "δεκα dh e1 k a0"
            is_shell_command: If True then we are not going to save the output rather than
                              just print it (so you can redirect it anywhere you want).
                              You shouldn't use this if you are using Windows (in Linux I had
                              some problems when calling the script from another bash script).
        Returns:
            The output lines of the new lexicon.
    """
    if check_dirs:
        out_path = _check_dir(path_to_file=path_to_words_txt, out_path=out_path, path_to_lexicon=path_to_lexicon)
    # Get lexicon hash map
    N = 3
    # Lexicon dictionary will be of the form:
    #   { "αυτ": {"αυτός": "a0 f t o1 s", "αυτοί": "a0 f t i1", ...}, ... }
    # This is done because the dictionary is huge and it's easier to handle it using a hash map.
    lexicon = Dictionary(path_to_lexicon, N)
    # Get words to transcribe
    with open(path_to_words_txt, "r", encoding="utf-8") as fr:
        lines = fr.readlines()
        out_lines: list = []
        for initial_word in lines:
            if initial_word.replace("\n", "").strip() == "":
                continue
            initial_word_complex = initial_word.strip()
            # Step 1: Make sure there are not spaces
            if " " in initial_word_complex:
                raise ValueError("Found space inside an entry of words.txt: {}.".format(initial_word_complex))
            # Step 2: Pre-processing and digit handling
            initial_word_complex = basic_preprocessing(initial_word_complex)
            # Step 3: Get rid of latin characters (if any). TODO: add more complex rules for english.
            edited_word_complex = initial_word_complex
            if english_mappings != {}:
                for letter in set(initial_word_complex):
                    if letter in english_mappings.keys():
                        edited_word_complex = re.sub(letter, english_mappings[letter], edited_word_complex)
            # The processing may have created more than one words (e.g. 102.4 -> εκατό δύο κόμμα τέσσερα)
            for initial_sub_word, edited_sub_word in zip(initial_word_complex.split(), edited_word_complex.split()):
                edited_sub_word = edited_sub_word.lower().strip()
                # Convert numbers to words
                if edited_sub_word.isdigit():
                    edited_sub_word = _number_to_word(edited_sub_word)
                    if not use_numbers:  # Then we are going to completely ignore numbers
                        out = ""
                        for edited_w in edited_sub_word.split():
                            # Use only the transliteration
                            out += lexicon.get_word_phonemes(word=edited_w, initial_word=None) + " "
                        out = re.sub(r"\s+", " ", out).strip()
                    else:
                        # If the number can be expressed in just one word then keep it.
                        # E.g. 1936 -> "χιλια εννιακοσια τριανταεξι" : more than 1 word so we won't keep the number
                        #      But 10 -> "δεκα" : only one word so we will keep the number 10
                        if len(edited_sub_word.split()) > 1:
                            out = ""
                            for edited_w in edited_sub_word.split():
                                # Use only the transliteration
                                out += lexicon.get_word_phonemes(word=edited_w, initial_word=None) + " "
                            out = re.sub(r"\s+", " ", out).strip()
                        elif len(edited_sub_word.split()) == 1:
                            # We expect the phonemes to correspond to only one word.
                            out = lexicon.get_word_phonemes(word=edited_sub_word, initial_word=initial_sub_word)
                        else:
                            # If we get here then there is probably some bug
                            warnings.warn("Error occurred while converting a digit: {}.".format(initial_sub_word))
                            continue
                else:
                    if len(edited_sub_word) == 1:  # single character
                        if edited_sub_word in single_letter_pronounciations.keys():
                            # E.g. convert "α" to "άλφα"
                            edited_sub_word = single_letter_pronounciations[edited_sub_word]

                        else:
                            warnings.warn("An unseen character has been observed while "
                                          "creating the lexicon: {}.".format(edited_sub_word))
                            continue
                    out = lexicon.get_word_phonemes(edited_sub_word, initial_word=initial_sub_word)
                out_lines.append(out)

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
    general_parser.add_argument("--use-numbers", default=False, choices=['True', 'true', True,
                                                                         'False', 'false', False],
                                help="If true then we will use numbers instead of 1-word numbers. This means "
                                     "that the number 10 will be written as '10 dh e1 k a0' instead of "
                                     "'δεκα dh e1 k a0' because 10 consists of only 1 word. But the number 1936 "
                                     "will be converted to the 3 words 'χιλια εννιακοσια τριανταεξι' since the "
                                     "word consists of more than 1 word.")
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

    if general_args.use_numbers.lower() in [True, 'true']:
        use_numbers = True
    else:
        use_numbers = False

    # ----------------------- CONVERT TEST WORD -----------------------------
    # If there is a test word then calculate its phonemes and exit
    if general_args.test_word != "":
        word = general_args.test_word
        print("Initial word:", word)
        word = basic_preprocessing(word)
        print("Processed word:", word)
        for sub_word in word.split():
            convert_word(sub_word)
        sys.exit(0)

    # --------------------------- USE LEXICON (RECOMMENDED) -----------------------------------
    # mode 1: Using the cmu lexicon
    lex_path = full_words_args.path_to_lexicon
    if full_words_args.path_to_words_txt != "." and os.path.exists(lex_path):
        out = convert_from_lexicon(full_words_args.path_to_words_txt,
                                   lex_path, general_args.out_path,
                                   check_dirs=True, use_numbers=use_numbers)
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
                     check_dirs=True, use_numbers=use_numbers)
        sys.exit(0)


if __name__ == '__main__':
    main()
