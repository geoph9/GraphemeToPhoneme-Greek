# MIT License
#
# Copyright (c) [year] [fullname]
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

import argparse
import os
import sys
import re


__basic_substitutes = {
    # GENERAL
    "4k": "φορ κέι", "λοιπον": "λοιπόν",
    # CURRENCIES
    "$": "δολλάρια", "€": "ευρώ",
    # PUNCTUATION
    "&": "και", "@": "παπάκι", "#": "δίεση", "%": "τοις εκατό", ",": "κόμμα",
    # PRONOUNS AND OTHERS
    "απο": "από", "μια": "μία", "ποιος": "ποιός", "ποια": "ποιά", "ποιο": "ποιό", "πιο": "πιό",
    # WORDS WITH MORE THAN ONE VOWEL THAT HAVE NO INTONATION
    "γεια": "γειά", "για": "γιά",
    "δυο": "δύο", "τρια": "τρία",  # NUMBERS
    "οκ": "οκέι", "okay": "οκέι", "ok": "οκέι",
    # INITIALS
    "ΚΤΕΟ": "κτέο", "ΕΟΠΥΥ": "εοπύ", "ΦΠΑ": "φιπιά", "Φ.Π.Α.": "φιπιά", 
    "VIP": "βι άι πι", "ΑΦΜ": "αφιμί", "Α.Φ.Μ.": "αφιμί", "Α.Φ.Μ": "αφιμί",
    "SMS": "εσεμές", 
    "ΑΜΚΑ": "άμκα", "Α.Μ.Κ.Α.": "άμκα", "Α.Μ.Κ.Α": "άμκα",
    # ENGLISH TO GREEK (GENERIC CASE)
    "service": "σέρβις", "courier": "κούριερ", "club": "κλάμπ", "portal": "πόρταλ", "app": "άπ",
    "mobile": "μομπάιλ", "username": "γιούζερνειμ", "password": "πασγουόρντ",
    "large": "λάρτζ", "medium": "μίντιουμ", "small": "σμόλ",
    "bye": "μπάι", "thank": "θενκ", "thanks": "θενκς", "you": "γιου", "yes": "γιές", "my": "μάι", 
    # COMPANIES
    "toyota": "τογιότα", "hyundai": "χιουντάι", "viber": "βάιμπερ", "Yamaha": "γιαμάχα",
    "Gant": "γκάντ", "Public": "πάμπλικ", 
    # WEB
    "online": "ονλάιν", "web": "γουέμπ", "site": "σάιτ", "website": "γουέμπσαιτ",
    "gr": "τζι αρ", "www": "ντάμπλ γιού ντάμπλ γιου ντάμπλ γιού", "com": "κόμ", 
    "email": "ιμέιλ", "e-mail": "ιμέιλ",
}


punctuation = [";", "!", ":", "∙", "»", ","]


def read_substitute_words(filepath):
    import json
    with open(filepath, "r", encoding='utf-8') as fr:
        content = fr.read()
        dictionary = json.loads(content)
    return dictionary


def _read_in_chunks(file_object, chunk_size=2048):
    """ Lazy function to read a file piece by piece. Useful for big files.
        Default chunk size: 2kB.
        Args: 
            file_object: An open file object.
            chunk_size: How many bytes to read on each chunk.
    """
    while True:
        data = file_object.readlines(chunk_size)
        if not data:
            break
        # a generator tuple
        data = ((l.split()[0].strip(), " ".join(l.split()[1:]).replace("\n", "").strip()) for l in data)
        yield data


def _check_dir(path_to_file: str, out_path: str, path_to_lexicon: str = None):
    # Assert lexicon existence
    if path_to_lexicon:
        if not os.path.exists(path_to_lexicon):
            raise FileNotFoundError("Could not locate the lexicon:", path_to_lexicon)
    # Check existence of words file
    if not os.path.exists(path_to_file):
        raise FileNotFoundError("Could not locate the path:", path_to_file)
    # Check if path to words.txt file is a directory
    if os.path.isdir(path_to_file):
        raise IsADirectoryError("Path to the text file is a directory: '" + path_to_file + "'")
    # Check if the out path is a directory or a file (if it's a file then the parent directory must exist)
    if os.path.isdir(out_path):
        # default filename
        out_path = os.path.join(out_path, "unknown_phonemes.txt")
    else:
        if not os.path.exists(os.path.dirname(out_path)):
            raise FileNotFoundError("Could not locate the directory where the output file will be saved:", out_path)
    return out_path


def handle_commas(word: str, comma_symbol=",") -> str:
    # If , (comma) is not between two numbers then erase it.
    comma_index = word.find(comma_symbol)
    while comma_index != -1:
        if comma_index == 0:
            word = word[1:]
        elif comma_index == len(word) - 1:  # if it is the last character
            if word[comma_index-1].isdigit():
                word = word.replace(comma_symbol, " κόμμα")  # e.g. if word=102, then we expect another digit after that
            else:
                word = word.replace(comma_symbol, "")
        else:
            word = re.sub(r"\s+", " ", word)
            # --------------- Start ignore spaces ---------------
            # So, for example, if word == 102 , 98 then convert it to 102, 98 and then to 102,98 (remove spaces)
            if word[comma_index-1] == " ":
                word = word[:comma_index-1] + word[comma_index:]
                comma_index -= 1  # The index went one place back
            try:
                if word[comma_index+1] == " ":
                    word = word[:comma_index+1] + word[comma_index+2:]
            except IndexError:
                pass
            # ----------------- End ignore spaces ----------------
            try:
                # Check left and right if they are digits
                if word[comma_index-1].isdigit() and word[comma_index+1].isdigit():
                    # if word=2,98 then convert it to δυο κόμμα ενενήντα οχτώ (keep the comma since it is pronounced)
                    word = word[:comma_index] + " κόμμα " + word[comma_index+1:]
                else:
                    # Otherwise, delete the comma
                    word = word[:comma_index] + " " + word[comma_index+1:]
            except IndexError:
                # Otherwise, delete the comma
                word = word[comma_index-1]
                break
        comma_index = word.find(comma_symbol)
    return word


def handle_hours(word: str):
    # We will assume that the word is an hour if it contains a ":"
    # For example, convert 10:45 to 10 και 45
    # If the minutes are 15 or 30 then the hour will look like:
    #   10:15 -> 10 και τεταρτο
    #   8:30  -> 8 και μιση (and not οχτωμιση)
    if ":" not in word:
        return word
    parts = word.split(":")
    if len(parts) != 2 or "" in parts:
        # Just ignore the ':'
        return re.sub(":", " ", word).strip()
    word = re.sub(":", " και ", word)
    if parts[1] == "15":
        word = re.sub("15", "τέταρτο", word)
    elif parts[1] == "30":
        word = re.sub("30", "μισή", word)
    return word


def process_word(word: str, keep_only_chars_and_digits: bool = True, to_lower: bool = True) -> str:
    word = word.strip()
    if to_lower:
        word = word.lower()
    for key, val in __basic_substitutes.items():
        key = key.lower()  # convert to lowercase in order to avoid bugs
        if (key in word.lower().split()) or (key in word.lower().split(".")):
            if key == "$": key = "\$"
            word = re.sub(key, " " + val + " ", word.lower().strip())
    word = re.sub(r"\.", " . ", word)
    word = re.sub(r"\?", " ? ", word)
    word = re.sub(r"•|∙|»", " ", word)
    if keep_only_chars_and_digits:
        word = re.sub(r"[^\w\d]", " ", word)  # Keep only characters and digits
    else:
        word = re.sub(r"\n", " \n ", word)
        word = re.sub(r"\t", " \t ", word)
        for char in punctuation:
            word = re.sub(char, " " + char + " ", word)
    word = re.sub(r"\s+", " ", word).strip()  # Remove redundant spaces
    return word


class InvalidPathError(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        prospective_dir = values
        if not os.path.exists(prospective_dir):
            raise argparse.ArgumentTypeError("InvalidPathError:{0} does not exist".format(prospective_dir))
        if os.access(prospective_dir, os.R_OK):
            setattr(namespace, self.dest, prospective_dir)
        else:
            raise argparse.ArgumentTypeError("InvalidPathError:{0} is not a readable dir".format(prospective_dir))
