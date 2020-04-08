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

import sys

import os
import glob
from tempfile import mkstemp
from shutil import move

import re
from g2p_greek.utils import process_word, handle_commas, punctuation

from g2p_greek.prefixes import _prefixes


to_plural = lambda word: re.sub("ερα", "ερις", re.sub("τρία", "τρείς", word))  # for 13 and 14 special cases in plural


def _check_input(number: str, length: int, operator: str = None):
    """ This function checks the validity of the inputs.
        Args:
            number: The number which we want to check (must be a string)
            length: The length of the number (how many digits it is allowed to have)
            operator: There are 3 choices:
                      1. None (default): Then there must be as many digits as the length argument (equation)
                      2. greater_equal (or ge): Then there must be at list *length* digits in the number
                      3. less_equal (or le): Then there must be at most *length* digits in the number
    """
    # Check input
    assert isinstance(number, str), "Input must be as string."
    if operator in ["greater_equal", "ge"]:
        assert len(number) >= length, "The digit must contain more than " + str(length) + " digits."
    elif operator in ["less_equal", "le"]:
        assert len(number) <= length, "The digit must contain less than " + str(length) + " digits."
    else:
        assert len(number) == length, "The digit must contain " + str(length) + " digits."


def _convert_1digit(number: str) -> str:
    _check_input(number, 1)
    if number not in _prefixes['1digit'].keys():
        raise ValueError("Digit", number, "is not a valid number.")
    out = _prefixes['1digit'][number]
    return out


def _convert_2digit(number: str) -> str:
    _check_input(number, 2)
    if number in _prefixes['2digit'].keys():  # so if it is 10 then return 'δέκα' (same for 11, 12 , 20, ..., 90)
        return _prefixes['2digit'][number]
    first_digit = number[0]  # e.g. from 15 keep only 1
    # Special case
    temp_num = number
    for index, sub_digit in enumerate(number):
        if sub_digit == "0":
            temp_num = number[index+1:]
        else:
            break
    number = temp_num
    if len(number) == 1:
        return _convert_1digit(number)  # If we had something like 01 then return the word for 1
    elif len(number) == 0:
        return ""  # If we had 00 then return nothing
    # Make sure that the 1st digit exists in the dictionary
    if first_digit not in _prefixes['2digit'].keys():
        raise ValueError("Invalid start:", first_digit, ". Occurred while converting the 2 digit number, ", number)
    # Return the 2 digit start and then call the _convert_1digit to convert the second number
    # E.g. 13 will become "δεκα" + "τρία" = "δεκατρία"
    out = _prefixes['2digit'][first_digit] + _convert_1digit(number[1])
    return out.strip()


def _convert_3digit(number: str) -> str:
    _check_input(number, 3)
    if number in _prefixes['3digit'].keys():  # E.g. if we have 300 then just return "τριακόσια"
        return _prefixes['3digit'][number]
    # Special case
    temp_num = number
    for index, sub_digit in enumerate(number):
        if sub_digit == "0":
            temp_num = number[index+1:]
        else:
            break
    number = temp_num
    if len(number) == 2:
        return _convert_2digit(number)  # If we had something like 012 then return the word for 12
    elif len(number) == 1:
        return _convert_1digit(number)  # If we had something like 001 then return the word for 1
    elif len(number) == 0:
        return ""  # If we had 00 then return nothing
    first_digit = number[0]  # e.g. from 387 keep 3
    # if first_digit == "0":
    #     return ""
    if first_digit not in _prefixes['3digit'].keys():
        raise ValueError("Invalid start:", first_digit, ". Occurred while converting the 3 digit number, ", number)
    # Return the 3 digit prefix and then the 2 digit prefix
    # E.g. for 387 return "τριακοσια" + " " + "ογδονταεφτά" = "τριακόσια ογδονταεφτά"
    out = _prefixes['3digit'][first_digit] + " " + _convert_2digit(number[1:])
    return out.strip()


def _convert_4digit(number: str) -> str:
    _check_input(number, 4)
    if number in _prefixes['4digit'].keys():  # E.g. if we have 7000 then just return "εφτά χιλιάδες"
        return _prefixes['4digit'][number]
    first_digit = number[0]  # e.g. from 7879 keep 7
    # Special case
    temp_num = number
    for index, sub_digit in enumerate(number):
        if sub_digit == "0":
            temp_num = number[index+1:]
        else:
            number = temp_num
            break
    if len(number) == 3:
        return _convert_3digit(number)  # If we had something like 0112 then return the word for 112
    elif len(number) == 2:
        return _convert_2digit(number)  # If we had something like 0012 then return the word for 12
    elif len(number) == 1:
        return _convert_1digit(number)  # If we had something like 0001 then return the word for 1
    elif len(number) == 0:
        return ""  # If we had 00 then return nothing
    # if first_digit == "0":
    #     return ""
    if first_digit not in _prefixes['4digit'].keys():
        raise ValueError("Invalid start:", first_digit, ". Occurred while converting the 4 digit number, ", number)
    # Return the 4 digit prefix and then the 4 digit prefix
    # E.g. for 7879 return "εφτά χιλιάδες" + " " + "οχτακόσια εβδομηνταεννιά" = "εφτά χιλιάδες οχτακόσια εβδομηνταεννιά"
    out = _prefixes['4digit'][first_digit] + " " + _convert_3digit(number[1:])
    return out.strip()


def _convert_5digit(number: str) -> str:
    _check_input(number, 5)
    if number in _prefixes['5digit'].keys():  # E.g. if we have 40000 then just return "σαράντα χιλιάδες"
        return _prefixes['5digit'][number]
    # Special case
    temp_num = number
    for index, sub_digit in enumerate(number):
        if sub_digit == "0":
            temp_num = number[index+1:]
        else:
            number = temp_num
            break
    if len(number) == 4:
        return _convert_4digit(number)  # If we had something like 01112 then return the word for 1112
    if len(number) == 3:
        return _convert_3digit(number)  # If we had something like 00112 then return the word for 112
    elif len(number) == 2:
        return _convert_2digit(number)  # If we had something like 00012 then return the word for 12
    elif len(number) == 1:
        return _convert_1digit(number)  # If we had something like 00001 then return the word for 1
    elif len(number) == 0:
        return ""  # If we had 00 then return nothing
    # At first find the 2 digit prefix -> e.g. from 89898 get the word for 89
    # Special case 13 and 14 where there needs to be a certain plural form (δεκατρείς χιλιάδες instead of δεκατρία).
    # Then append the word "χιλιάδες"
    # Then append the 3 digit leftover from _convert_3digit -> e.g. from 78123 get the word for 123
    out = to_plural(_convert_2digit(number[:2])) + " χιλιάδες " + _convert_3digit(number[2:])
    return out.strip()


def _convert_6digit(number: str) -> str:
    _check_input(number, 6)
    if number in _prefixes['6digit'].keys():  # E.g. if we have 400000 then just return "σαράντα χιλιάδες"
        return _prefixes['6digit'][number]
    # Special case
    temp_num = number
    for index, sub_digit in enumerate(number):
        if sub_digit == "0":
            temp_num = number[index+1:]
        else:
            break
    number = temp_num
    if len(number) == 5:
        return _convert_5digit(number)  # If we had something like 012112 then return the word for 12112
    if len(number) == 4:
        return _convert_4digit(number)  # If we had something like 001112 then return the word for 1112
    if len(number) == 3:
        return _convert_3digit(number)  # If we had something like 000112 then return the word for 112
    elif len(number) == 2:
        return _convert_2digit(number)  # If we had something like 000012 then return the word for 12
    elif len(number) == 1:
        return _convert_1digit(number)  # If we had something like 000001 then return the word for 1
    elif len(number) == 0:
        return ""  # If we had 00 then return nothing
    # Steps:
    # 1. Check if the number is in the form 000000 (can happen). If so then return nothing
    # 2. At first find the 3 digit prefix -> e.g. from 131789 get the word for 131
    # 3. Special case *13 and *14 where there needs to be a certain plural form (δεκατρείς χιλιάδες instead of δεκατρία)
    # 4. Then append the word "χιλιάδες"
    # 5. Then append the 3 digit leftover from _convert_3digit -> e.g. from 131789 get the word for 789
    last_3_digits = _convert_3digit(number[3:])
    if number[:3] == "000":
        return last_3_digits  # e.g. if input is 000183 return εκατόν ογδοντατρία
    first_3_digits = to_plural(_convert_3digit(number[:3]))
    out = first_3_digits + " χιλιάδες " + last_3_digits
    return out.strip()


def _convert_more_than7_less_than10_digits(number: str) -> str:
    # From 1000000 (1 million) to 1000000000 (1 billion)
    _check_input(number, 7, operator="greater_equal")
    _check_input(number, 9, operator="less_equal")
    # There is one special case since 1000000 (1 million) wants singular form
    if len(number) == 7 and number[0] == "1":
        out = "ένα εκατομμύριο " + _convert_6digit(number[1:])
        return out
    # --------------------------------- SPECIAL CASE ----------------------------------
    # Special case: if called from a larger number then there is a possibility to have all zeroes
    # E.g. for 3 billion we are going to have a 3 and 9 zeroes after that. We don't want to append "εκκατομυριο" to that
    temp_num = number
    for index, sub_digit in enumerate(number):
        if sub_digit == "0":
            temp_num = number[index+1:]  # e.g. if number=0010000 then it will be converted to 10000
        else:
            break
    number = temp_num
    # number = re.sub("0", "", temp_num)
    if len(number) == 6:
        out = _convert_6digit(number)
    elif len(number) == 5:
        out = _convert_5digit(number)
    elif len(number) == 4:
        out = _convert_4digit(number)
    elif len(number) == 3:
        out = _convert_3digit(number)
    elif len(number) == 2:
        out = _convert_2digit(number)
    elif len(number) == 1:
        out = _convert_1digit(number)
    elif len(number) == 0:
        return ""
    # --------------------------------- END SPECIAL CASE ----------------------------------

    if len(number) == 7:
        out = _convert_1digit(number[0]) + " εκατομμύρια " + _convert_6digit(number[1:])
    elif len(number) == 8:
        out = _convert_2digit(number[:2]) + " εκατομμύρια " + _convert_6digit(number[2:])
    elif len(number) == 9:
        out = _convert_3digit(number[:3]) + " εκατομμύρια " + _convert_6digit(number[3:])
    return out.strip()


def _convert_more_than10_less_than13_digits(number: str) -> str:
    # From 1 billion to 1 trillion
    _check_input(number, 10, operator="greater_equal")
    _check_input(number, 12, operator="less_equal")
    # There is one special case since 1000000 (1 million) wants singular form
    if len(number) == 10 and number[0] == "1":
        out = "ένα δισεκατομμύριο " + _convert_more_than7_less_than10_digits(number[1:])
        return out
    if len(number) == 10:
        out = _convert_1digit(number[0]) + " δισεκατομμύρια " + _convert_more_than7_less_than10_digits(number[1:])
    elif len(number) == 11:
        out = _convert_2digit(number[:2]) + " δισεκατομμύρια " + _convert_more_than7_less_than10_digits(number[2:])
    elif len(number) == 12:
        out = _convert_3digit(number[:3]) + " δισεκατομμύρια " + _convert_more_than7_less_than10_digits(number[3:])
    return out.strip()


def convert_numbers(initial_word: str) -> str:
    word = process_word(initial_word)
    # print(word)
    if not word.isdigit():
        return initial_word
    else:
        if len(word) == 1:
            return _convert_1digit(word)
        elif len(word) == 2:
            return _convert_2digit(word)
        elif len(word) == 3:
            return _convert_3digit(word)
        elif len(word) == 4:
            return _convert_4digit(word)
        elif len(word) == 5:
            return _convert_5digit(word)
        elif len(word) == 6:
            return _convert_6digit(word)
        elif 7 <= len(word) <= 9:  # from 1 million to 999999999
            return _convert_more_than7_less_than10_digits(word)
        elif 10 <= len(word) <= 12:  # from 1 billion to 999 999 999 999
            return _convert_more_than10_less_than13_digits(word)
        else:
            raise ValueError("We only accept integers of maximum 13 digits")


def convert_sentence(sentence: str):
    sentence = handle_commas(sentence)
    # sentence = re.sub(r"\.", " . ", sentence)
    sentence = process_word(sentence, remove_unknown_chars=False, to_lower=False)
    final_sent = []
    for word in sentence.split():
        final_sent.append(convert_numbers(word))
    # Concatenate punctuation (e.g. from "they had 9 . the others had 10 ." to "they had nine. the others had 10.")
    final_sent = " ".join(final_sent)
    final_sent = re.sub(r"\s\.", ".", final_sent)
    final_sent = re.sub(r"\s\?", "?", final_sent)
    final_sent = re.sub(r"\s\n", "\n", final_sent)
    final_sent = re.sub(r"\s\t", "\t", final_sent)
    for char in punctuation:
        final_sent = re.sub(" " + char, char, final_sent)
    final_sent = re.sub(":", " ", final_sent)
    final_sent = re.sub(r"\s+", " ", final_sent)
    return final_sent


def _replace_file_contents(filepath: str):
    """
        Args:
            filepath: The path to the file for which you want to change the numbers to words.
        Returns:
            Nothing
    """
    # ------------------------ CHECK IF FILE EXISTS ---------------------------
    if not os.path.exists(filepath):
        raise FileNotFoundError("Could not locate the path that you provided:", filepath)
    # ----------------------------- REPLACE FILE -------------------------------
    # Create temporary file which will replace the old one.
    fh, abs_path = mkstemp()
    with os.fdopen(fh, 'w') as newf:
        with open(filepath, "r", encoding="utf-8") as f:
            text = convert_sentence(f.read())
            newf.write(text)
    # Remove old file
    os.remove(filepath)
    # Move new file
    move(abs_path, filepath)


def convert_kaldi_text(kaldi_text_path, is_shell_command = False):
    assert os.path.isfile(kaldi_text_path), "Path to the kaldi text file does not exist " \
                                            "or is a directory: {}.".format(kaldi_text_path)
    new_lines = []
    fh, abs_path = mkstemp()
    with os.fdopen(fh, 'w') as newf:
        with open(kaldi_text_path, "r", encoding="utf-8") as fr:
            line = fr.readline()
            while line:
                utt_id = line.split()[0]
                line = " ".join(line.split()[1:]).strip().replace("\n", "")  # get rid of the utt_id
                new_line = convert_sentence(line)
                new_line = utt_id + " " + new_line + "\n"
                if is_shell_command is True:
                    new_lines.append(new_line)
                else:
                    newf.write(new_line)
                line = fr.readline()
    if is_shell_command is False:
        # Remove old file
        os.remove(kaldi_text_path)
        # Move new file
        move(abs_path, kaldi_text_path)
    return new_lines


def main():
    msg = """ Use this script if you want to convert the digits of a file to their equivalent greek words.
              You may provide a path to a text file containing only the transcript of an audio file and the 
              contents of it will be replace with so that there are not digits.
              E.g. If the file contains "100 ευρώ" then it will be converted to "εκατό ευρώ"
              
              You may also provide the path to a directory where transcript files are located and the script 
              will process all of them. Make sure to change the file extension if needed since the default 
              one is .lab. 
              
              If you want to test the script then you may use the -t argument and provide a single word.
              
              NOTE: The files are replaced so please be careful to have a copy of the original ones before
              you run this script.
            
          """
    parser = argparse.ArgumentParser(description=msg)
    parser.add_argument("-p", "--path", required=False, default="./files/",
                        help="Path to a file or a directory containing the text files.")
    parser.add_argument("-e", "--extension", required=False, default=".lab",
                        help="Extension of the text files containing the transcripts.")
    parser.add_argument("--kaldi-text", required=False, default=None,
                        help="Path to a kaldi text file. This means that the format will "
                             "comply with: utt_id word1 word2 ... wordN")
    parser.add_argument("--shell-command", action="store_true", dest="is_shell_command",
                        help="If provided then we will redirect the output to stdout and "
                             "then you can handle that from your bash script.")
    parser.set_defaults(is_shell_command=False)
    parser.add_argument("-t", "--test-word", required=False, default="NONE",
                        help="A test word in order to test the functionality of the script.")
    args = parser.parse_args()
    if args.test_word != "NONE":
        print(convert_sentence(args.test_word))
        print("Converted test word, now exiting...")
        sys.exit(1)
    if args.kaldi_text is not None:
        out = convert_kaldi_text(args.kaldi_text, args.is_shell_command)
        if args.is_shell_command is True:
            print("".join(out))
        else:
            print("Successfully converted kaldi text entries!")
        sys.exit(0)
    filepath = args.path
    if filepath == "./files/":
        print("Using the default filepath:", filepath, ". If you want to use another "
                                                       "path do so by using the "
                                                       "--path argument.")
    # ------------------------ CASE 1: INPUT IS FILE ---------------------------
    if os.path.isfile(filepath):
        # Create temporary file which will replace the old one.
        _replace_file_contents(filepath)
        print("Success!")
        print("Done processing file from the file:", filepath)
        sys.exit(1)
    # ------------------------ CASE 2: INPUT IS DIR ---------------------------
    if os.path.isdir(filepath):
        text_file_dir = glob.glob(os.path.join(filepath, "*" + args.extension))
        if len(text_file_dir) == 0:
            raise ValueError("The directory that you provided is empty")
        for text_file in text_file_dir:
            _replace_file_contents(text_file)
        print("Success!")
        print("Done processing files from the directory:", filepath)
        sys.exit(1)
    print("Error")
    print("Something happened and there were no changes made...")


if __name__ == '__main__':
    main()
    # test = "είχα 113,5 ευρώ και έγιναν 9; Πιο παλιά είχα 2184$. Ένας άλλος είχε 113914 ευρώ. ο μέσσι παίρνει " \
    #        "30000000 τον χρόνο. άρα σε 100 χρόνια θα μαζέψει 3000000000 ευρώ."
    # # test = "300000000001"
    # # test = "102,45"
    #
    # print(convert_sentence(test))
