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
from string import punctuation as valid_punctuation

from g2p_greek.rules import *
from g2p_greek.utils import process_word, _check_dir, InvalidPathError, handle_commas, handle_hours, read_substitute_words
try:
    from num2word.utils import convert_ordinals
    from num2word.convert_numbers import convert_numbers
except ImportError:
    convert_ordinals = lambda x: x
    from g2p_greek.digits_to_words import convert_numbers

from g2p_greek.dictionary import Dictionary
from g2p_greek.phoneme_conversion import convert_word

try:
    from g2p_greek.english_rules import english_mappings
except ImportError:
    english_mappings = {}
    pass


def basic_preprocessing(initial_word: str, to_lower: bool = True, punctuation_to_keep: list = [],
                        substitute_words_dict: dict = None):
    """ Basic preprocessing. Here we assume that the input (word) is a
        single word and does not contain any spaces in it. This is normal
        since, supposedly, the input is each line in a words.txt file
        (and each line is a single word by default).
        Note that this function does not convert numbers to words. (except from 10ος -> δέκατος etc)
        Args:
            initial_word: A single word.
            punctuation_to_keep: Checp the process_word method in utils.py
        Returns:
            The processed outcome of the word. May be more than one words.
            For example, if the input is "10,9" then is will be converted to
            "10 κόμμα 9" (decimal handling).
    """
    initial_word = re.sub(r"\s\t", "\t", initial_word)
    if to_lower: initial_word = initial_word.lower()
    word_complex = handle_commas(initial_word).strip()
    word_complex = handle_hours(word_complex)
    # A list of hyphens taken from here: http://jkorpela.fi/dashes.html
    word_complex = re.sub(r"-|-|-|~|֊|᠆|‐|‑|‒|–|—|―|⁓|⁻|₋|−|〜|﹘|﹣|－", " ", word_complex)
    # Convert ordinals (if the num2word package is installed)
    word_complex = convert_ordinals(word_complex)
    # print(word_complex)
    new_word = ""
    for word in word_complex.split():
        # ----- BASIC PROCESSING -----
        word = process_word(word, to_lower=False, keep_only_chars_and_digits=True, 
                            basic_substitutes=substitute_words_dict, punctuation_to_keep=punctuation_to_keep)
        for sub_word in word.split():
            if sub_word.strip() == "":
                continue
            # Split words into words and digits (numbers). E.g. είναι2 -> είναι 2
            words = re.split(r"(\d+)", sub_word)  # may have spaces
            words = [w for w in words if w.strip() != ""]  # remove spaces from list
            for w in words:
                new_word += w + " "
        new_word += " "
    new_word = re.sub(r"\s+", " ", new_word).strip()
    return new_word


def _number_to_word(number: str) -> str:
    """
        Args:
            number: A string that should match to a number.
        Returns: the corresponding word.
        Raises: ValueError if the argument is not a digit.
    """
    if not number.isdigit(): raise ValueError("Not a number: {}.".format(number))
    return convert_numbers(number)


class G2P(object):
    def __init__(self, words_txt_path: str = None, out_path: str = None, is_shell_command: bool = False, use_numbers: bool = False,
                 lexicon_path: str = None, substitute_words_path: str = None, N: int = 3, test_mode: bool = False, punc_to_keep=""):
        """ Finds the phonemes of a list of unknown words from a file in this format:
                word1
                word2
                ...
            Saves a new file in the following format:
                word1 phone1 phone2 ... phoneN
                word2 phone1 phone2 ... phoneN
            Args:
                words_txt_path: The path to the words.txt file which should contain
                                one word per line.
                lexicon_path: The path to the lexicon which should contain some previous
                              knowledge on the phonemes of certain words. If available,
                              you should provide the CMU Greek dictionary (el-gr.dic).
                out_path: The path to where the lexicon output will be saved.
                use_numbers: If False then all numbers will be converted to words before writing
                             them to the lexicon. Otherwise, the lexicon will contain the numbers.
                             E.g. If True then the word 10 will be written as "10 dh e1 k a0"
                                  If False then the word 10 will be written as "δεκα dh e1 k a0"
                is_shell_command: If True then we are not going to save the output rather than
                                  just print it (so you can redirect it anywhere you want).
                                  You shouldn't use this if you are using Windows (in Linux I had
                                  some problems when calling the script from another bash script).
                substitute_words_path: Path to a json or a csv file containing matchings of words to their 
                                       transliteration (e.g. {"mercedes": "μερσέντες", "ok": "οκέι", ...}).
                                       If None then we won't substitute any word.
                test_mode: True if we are in test mode (check --test-word or -t in the arguments).
            Returns:
                The output lines of the new lexicon.
        """
        if isinstance(punc_to_keep, str):
            punc_to_keep = list(punc_to_keep)
        assert isinstance(punc_to_keep, list)
        if not set(punc_to_keep) <= set(list(valid_punctuation)):  # if the punctuation provided is not a subset of the valid punctuation
            raise argparse.ArgumentTypeError("Invalid punctuation was provided in --punctuation-to-keep.")
        if test_mode is False:
            self.out_path = _check_dir(path_to_file=words_txt_path, out_path=out_path, path_to_lexicon=lexicon_path)
        self.words_path = words_txt_path
        self.lexicon_path = lexicon_path
        self.lexicon = None  # will be initialize when convert_from_lexicon is called
        self.substitute_words_dict = read_substitute_words(substitute_words_path)
        self.is_shell_command = is_shell_command
        self.use_numbers = use_numbers
        self.N = N
        self.punc_to_keep = punc_to_keep

    def initialize_lexicon(self):
        self.lexicon =  Dictionary(self.lexicon_path, self.N)

    @staticmethod
    def convert_latin_chars(sentence):
        edited_sentence = sentence
        if english_mappings != {}:
            for letter in set(sentence):
                if letter in english_mappings.keys():
                    edited_sentence = re.sub(letter, english_mappings[letter], edited_sentence)
        return edited_sentence

    def _convert_from_list(self, lines):
        out_lines: list = []
        for i, initial_word in enumerate(lines):
            if initial_word.replace("\n", "").strip() == "":
                continue
            initial_word_complex = initial_word.strip()
            # Step 1: Make sure there are not spaces
            if " " in initial_word_complex:
                raise ValueError("Found space inside an entry of words.txt.\nLine: {}\nWord: {}.".format(i, initial_word_complex))
            # Step 2: Pre-processing and digit handling
            initial_word_complex = basic_preprocessing(initial_word_complex, substitute_words_dict=self.substitute_words_dict, punctuation_to_keep=self.punc_to_keep)
            # Step 3: Get rid of latin characters (if any). TODO: add more complex rules for english.
            edited_word_complex = self.convert_latin_chars(initial_word_complex)
            # The processing may have created more than one words (e.g. 102.4 -> εκατό δύο κόμμα τέσσερα)
            for initial_sub_word, edited_sub_word in zip(initial_word_complex.split(), edited_word_complex.split()):
                edited_sub_word = edited_sub_word.lower().strip()
                # Convert numbers to words
                if edited_sub_word.isdigit():
                    edited_sub_word = _number_to_word(edited_sub_word)
                    if not self.use_numbers:  # Then we are going to completely ignore numbers
                        out = ""
                        for edited_w in edited_sub_word.split():
                            if self.lexicon is None:  # there are very few iterations, so we can put this if inside the for loop
                                _, current_phones = convert_word(edited_w)  # Get word and phonemes
                                # Use only the transliteration
                                out += edited_w + " " + " ".join(current_phones) + "\n"  # append new line at the end
                            else:
                                # Use only the transliteration
                                out += self.lexicon.get_word_phonemes(word=edited_w, initial_word=None) + " "
                        out = re.sub(r"\s+", " ", out).strip()
                    else:                            
                        # If the number can be expressed in just one word then keep it.
                        # E.g. 1936 -> "χιλια εννιακοσια τριανταεξι" : more than 1 word so we won't keep the number
                        #      But 10 -> "δεκα" : only one word so we will keep the number 10
                        if len(edited_sub_word.split()) > 1:
                            out = ""
                            for edited_w in edited_sub_word.split():
                                # Use only the transliteration
                                if self.lexicon is None:
                                    _, current_phones = convert_word(edited_w)  # Get word and phonemes
                                    out += edited_w + " " + " ".join(current_phones) + "\n"  # append new line at the end
                                else:
                                    out += self.lexicon.get_word_phonemes(word=edited_w, initial_word=None) + " "
                            out = re.sub(r"\s+", " ", out).strip()
                        elif len(edited_sub_word.split()) == 1:
                            if self.lexicon is None:
                                # We expect the phonemes to correspond to only one word.
                                _, current_phones = convert_word(edited_sub_word)  # Get word and phonemes
                                out = edited_sub_word + " " + " ".join(current_phones) + "\n"  # append new line at the end
                            else:
                                # We expect the phonemes to correspond to only one word.
                                out = self.lexicon.get_word_phonemes(word=edited_sub_word, initial_word=initial_sub_word)
                        else:
                            # If we get here then there is probably some bug
                            warnings.warn("Error occurred while converting a digit: {}.".format(initial_sub_word))
                            continue
                else:
                    if len(edited_sub_word) == 1:  # single character
                        if edited_sub_word in single_letter_words:
                            pass
                        elif edited_sub_word in single_letter_pronounciations.keys():
                            # E.g. convert "α" to "άλφα"
                            edited_sub_word = single_letter_pronounciations[edited_sub_word]
                        elif edited_sub_word in self.punc_to_keep:
                            continue
                        else:
                            warnings.warn("An unseen character has been observed while "
                                          "creating the lexicon: {}.".format(edited_sub_word))
                            continue
                    if self.lexicon is None:
                        _, current_phones = convert_word(edited_sub_word)  # Get word and phonemes
                        out = initial_sub_word + " " + " ".join(current_phones) + "\n"  # append new line at the end
                    else:
                        out = self.lexicon.get_word_phonemes(edited_sub_word, initial_word=initial_sub_word)
                out = out.strip()
                if not out.endswith("\n"): out += "\n"
                out_lines.append(out)
        return list(set(out_lines))  # remove duplicates

    def convert_from_lexicon(self):
        # Lexicon dictionary will be of the form:
        #   { "αυτ": {"αυτός": "a0 f t o1 s", "αυτοί": "a0 f t i1", ...}, ... }
        # This is done because the dictionary is huge and it's easier to handle it using a hash map.
        self.initialize_lexicon()
        # Get words to transcribe
        with open(self.words_path, "r", encoding="utf-8") as fr:
            lines = fr.readlines()
            out_lines = self._convert_from_list(lines)
        if not self.is_shell_command:
            # Write the new lines
            with open(os.path.abspath(self.out_path), "w", encoding="utf-8") as fw:
                for line in out_lines:
                    fw.write(line)
        return out_lines

    def convert_file(self):
        # Read input file
        with open(self.words_path, "r", encoding="utf-8") as fr:
            lines = fr.readlines()
            out_lines = self._convert_from_list(lines)
        if not self.is_shell_command:
            # Write the new lines
            with open(os.path.abspath(self.out_path), "w", encoding="utf-8") as fw:
                for line in out_lines:
                    fw.write(line)
        return out_lines

    def convert_test_word(self, initial_word):
        line_list = initial_word.split("\\n")  # convert to line (can also accept multiple lines separated by \n)
        out_lines = self._convert_from_list(line_list)
        return out_lines

    def convert(self):
        # Uses the default behaviour which is using the CMU dictionary.
        return self.convert_from_lexicon



def cmdline():
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
    general_parser.add_argument("-o", "--out-path", required=False, default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tests", "output.dic"),
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
    general_parser.add_argument("--substitute-words-path", "-s", action=InvalidPathError, default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "substitute_words.json"), 
                                help="Path to a json or CSV file containing matchings from words to their transliteration in Greek."
                                     "For example, {'mercedes': 'μερσέντες', 'ok': 'οκέι', ...}")
    general_parser.add_argument("--punctuation-to-keep", type=str, default="", dest="punc_to_keep",
                                help="A sequence of punctuations you want to keep (without spaces)")
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
    full_words_parser.add_argument("-w", "--path-to-words-txt", required=False, default=None, action=InvalidPathError,
                                   help="Path to the words.txt file (or any other name) that contains all of the words"
                                        "that appear in our data (e.g. in the kaldi text file).")
    full_words_parser.add_argument("-l", "--path-to-lexicon", required=False, default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "el-gr.dic"),
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

    if general_args.use_numbers in [True, 'true', 'True']:
        use_numbers = True
    else:
        use_numbers = False
    # ----------------------- CONVERT TEST WORD -----------------------------
    # If there is a test word then calculate its phonemes and exit
    if general_args.test_word != "":
        word = general_args.test_word
        g2p = G2P(test_mode=True, substitute_words_path=general_args.substitute_words_path, 
                  use_numbers=use_numbers, punc_to_keep=general_args.punc_to_keep)
        out = g2p.convert_test_word(word)
        print(out)
        sys.exit(0)

    # --------------------- NON TEST MODES ------------------------
    if full_words_args.path_to_words_txt is not None:
        words_txt_path = full_words_args.path_to_words_txt
    elif unknown_words_args.path_to_unknown_words is not None:
        words_txt_path = unknown_words_args.path_to_unknown_words
    else:
        raise ValueError("Could not initialize the path to the words.txt file. Something must be wrong with the arguments.")
    g2p = G2P(words_txt_path, general_args.out_path, is_shell_command=general_args.is_shell_command, 
              use_numbers=use_numbers, lexicon_path=full_words_args.path_to_lexicon, 
              substitute_words_path=general_args.substitute_words_path, N=3, punc_to_keep=general_args.punc_to_keep)

    # --------------------------- USE LEXICON (RECOMMENDED) -----------------------------------
    # mode 1: Using the cmu lexicon
    if (full_words_args.path_to_words_txt is not None) and (os.path.isfile(full_words_args.path_to_lexicon)):
        out = g2p.convert_from_lexicon()
        if general_args.is_shell_command:
            print("".join(out))
        else:
            print("Success! File saved in: {}".format(general_args.out_path))
        sys.exit(0)

    # ---------------------------------- USE OUR ALGORITHM ---------------------------------
    # mode 2: Do not use the lexicon
    if unknown_words_args.path_to_unknown_words != ".":
        out = g2p.convert_file()
        if general_args.is_shell_command:
            print("".join(out))
        else:
            print("Success! File saved in: {}".format(general_args.out_path))
        sys.exit(0)


if __name__ == '__main__':
    cmdline()
