import re
from g2p_own_rules import process_sentence


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

_prefixes = {
    "1digit": {
        "0": "μηδέν",
        "1": "ένα",  # μια, ένας
        "2": "δύο",
        "3": "τρία",  # τρεις
        "4": "τέσσερα",  # τέσσερις
        "5": "πέντε",
        "6": "έξι",
        "7": "εφτά",
        "8": "οχτώ",
        "9": "εννιά"
    },
    "2digit": {
        "10": "δέκα",
        "11": "έντεκα",
        "12": "δώδεκα",
        "1": "δεκα",
        "20": "είκοσι",
        "2": "εικοσι",
        "30": "τριάντα",
        "3": "τριαντα",
        "40": "σαράντα",
        "4": "σαραντα",
        "50": "πενήντα",
        "5": "πενηντα",
        "60": "εξήντα",
        "6": "εξηντα",
        "70": "εβδομήντα",
        "7": "εβδομηντα",
        "80": "ογδόντα",
        "8": "ογδοντα",
        "90": "ενενήντα",
        "9": "ενενηντα"
    },
    "3digit": {
        "100": "εκατό",
        "1": "εκατον",
        "200": "διακόσια",
        "2": "διακοσια",
        "300": "τριακόσια",
        "3": "τριακοσια",
        "400": "τετρακόσια",
        "4": "τετρακοσια",
        "500": "πεντακόσια",
        "5": "πεντακοσια",
        "600": "εξακόσια",
        "6": "εξακοσια",
        "700": "εφτακόσια",
        "7": "εφτακοσια",
        "800": "οχτακόσια",
        "8": "οχτακοσια",
        "900": "εννιακόσια",
        "9": "εννιακοσια",
    }
}

_plural_forms = {
    "0": "μηδέν",
    "1": "ένα",
    "2": "δυο",
    "3": "τρεις",
    "4": "τέσσερις",
    "5": "πέντε",
    "6": "έξι",
    "7": "εφτά",
    "8": "οχτώ",
    "9": "εννιά"
}

# Update with 4 digits
_prefixes['4digit'] = {'1': 'χίλια'}
_prefixes['4digit'].update({key: (_plural_forms[key] + " χιλιάδες").strip() for key, val in _prefixes['1digit'].items()
                            if key != "1"})

# For 10, 11, 12, 20, 30, 40, ..., 90 take the prefixes from the 2 digit pronunciations
#   and convert them to 10000, 11000, 12000, 20000, ..., 90000
_prefixes['5digit'] = {key + "000": val + " χιλιάδες" for key, val in _prefixes['2digit'].items() if len(key) > 1}

# Update for 6 digits. Replace "διακόσια" with "διακόσιες" in order to bring to plural form
_prefixes['6digit'] = {key + "000": val[:-2] + "ιες" + " χιλιάδες" for key, val in _prefixes['3digit'].items()}


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
    if first_digit == "0":
        return ""
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
    first_digit = number[0]  # e.g. from 387 keep 3
    if first_digit == "0":
        return ""
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
    if first_digit == "0":
        return ""
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
    # At first find the 2 digit prefix -> e.g. from 89898 get the word for 89
    # Special case 13 and 14 where there needs to be a certain plural form (δεκατρείς χιλιάδες instead of δεκατρία).
    # Then append the word "χιλιάδες"
    # Then append the 3 digit leftover from _convert_3digit -> e.g. from 78123 get the word for 123
    out = to_plural(_prefixes['2digit'][number[:2]]) + " χιλιάδες " + _convert_3digit(number[2:])
    return out.strip()


def _convert_6digit(number: str) -> str:
    _check_input(number, 6)
    if number in _prefixes['6digit'].keys():  # E.g. if we have 400000 then just return "σαράντα χιλιάδες"
        return _prefixes['6digit'][number]
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
    for index, sub_digit in enumerate(number):
        if sub_digit == "0":
            number = number[index:]  # e.g. if number=0010000 then it will be converted to 10000
        else:
            break
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
        out = "ένα δισεκατομμύριο " + _convert_6digit(number[1:])
        return out
    if len(number) == 10:
        out = _convert_1digit(number[0]) + " δισεκατομμύρια " + _convert_more_than7_less_than10_digits(number[1:])
    elif len(number) == 11:
        out = _convert_2digit(number[:2]) + " δισεκατομμύρια " + _convert_more_than7_less_than10_digits(number[2:])
    elif len(number) == 12:
        out = _convert_3digit(number[:3]) + " δισεκατομμύρια " + _convert_more_than7_less_than10_digits(number[3:])
    return out.strip()


def convert_numbers(word: str) -> str:
    word = process_sentence(word)
    if not word.isdigit():
        return word
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
    # sentence = process_sentence(sentence)
    final_sent = []
    for word in sentence.split():
        final_sent.append(convert_numbers(word))
    return " ".join(final_sent)


if __name__ == '__main__':
    test = "είχα 113 ευρώ και έγιναν 9. Πιο παλιά είχα 2184$. Ένας άλλος είχε 113914 ευρώ. ο μέσσι παίρνει " \
           "30000000 τον χρόνο. άρα σε 100 χρόνια θα μαζέψει 3000000000 ευρώ."
    # test = "3000000000"
    # test = "30000000"
    print(convert_sentence(test))
