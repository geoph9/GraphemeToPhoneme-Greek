import argparse
import os
import re


__basic_substitutes = {
    "4k": "φορ κέι",
    "$": "δολλάρια",
    "€": "ευρώ",
    "&": "και",
    "@": "παπάκι",  # ατ
    "#": "δίεση",  # χασταγκ
    "%": "τοις εκατό",
    ",": "κόμμα"
}


punctuation = [";", "!"]


def _read_in_chunks(file_object, chunk_size=2048):
    """
    Lazy function to read a file piece by piece.
    Default chunk size: 2kB.
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
            raise FileNotFoundError("Could not locate the directory where the output file will be saved.")
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


def process_word(word: str, remove_unknown_chars: bool = True, to_lower: bool = True) -> str:
    if to_lower:
        word = word.lower()
    for key, val in __basic_substitutes.items():
        if key in word.lower():
            word = re.sub(key, " " + val + " ", word.lower())
    if remove_unknown_chars:
        word = re.sub(r"[^\w\d]", " ", word)  # Keep only characters and digits
    else:
        word = re.sub(r"\.", " . ", word)
        word = re.sub(r"\?", " ? ", word)
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
