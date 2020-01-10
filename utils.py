import argparse
import os


def load_lexicon(path_to_lexicon: str) -> dict:
    with open(path_to_lexicon, "r", encoding="utf-8") as fr:
        lex_dict = fr.readlines()
        lex_dict = {str(entry.split()[0]): " ".join(entry.split()[1:]) for entry in lex_dict}
    return lex_dict


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


def process_sentence(word: str) -> str:
    word = " ".join([re.sub(key, val, word) for key, val in basic_substitutes.items()])
    word = re.sub(r"[^\w\d]", " ", word)  # Keep only characters and digits
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
