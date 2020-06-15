# Grapheme To Phoneme Conversion For Greek

This repository contains code for converting words to their
corresponding phonemes. In addition, there is functionality
to convert numbers to words (e.g. 10 -> δέκα) up until 
`10^13 - 1` (1 trillion minus one).

The conversion from words to phonemes is done in 3 stages.
1. Convert single characters to their corresponding phonemes
2. Locate diphthongs and replace the previous content
3. Sanity check to make sure that the same vowels do not appear
consecutively and that there is at least one intonated phoneme 
in each word.

The rules for changing the words to their phonemes are taken 
from the greek lexicon provided at the CMU Sphinx website 
[here](https://sourceforge.net/projects/cmusphinx/files/Acoustic%20and%20Language%20Models/Greek/).
The lexicon is already downloaded in the `./data/` folder so 
you don't need to re-download it if you have cloned this repo.

*NOTE 1:* This is not 100% accurate and it may lead to mistakes. 
After using the scripts please check the output in order to 
make sure that everything went well since there is a chance 
that you may need to change something by hand.

*NOTE 2:* This repository has been created in order to help me 
handle out of vocabulary (OOV) words while creating a kaldi model.
Feel free to change it and adjust it to your needs, though you must 
be careful, since, as I said, the code has not been tested in different
corpora.

## Installation:

In order to install this repository as a package, do the following:

```
git clone https://github.com/geoph9/GraphemeToPhoneme-Greek.git
cd GraphemeToPhoneme-Greek
pip install -e .
```

If no error occurs then you are fine. To make sure, you may run: 
`python -c "import g2p_greek"`. If that works, then you may use 
this repo as a package.

## How to use

After installation you may use the `g2p_greek.py` script for your word-to-phoneme 
conversion. There is also the `digits_to_words.py` script which has been deprecated.
The [Numbers2Words-Greek](https://github.com/geoph9/Numbers2Words-Greek) repository 
is more stable. Just clone it and install it and we are going to use that instead of 
`digits_to_words.py`. Below, I will try to give a brief introduction on the main points 
of these scripts.


## The `g2p_greek.py` script:
This script contains functionality to find the phonemes of greek words.
The algorithms uses only rules and does not need anything to learn. Since 
there are always irregularities, this algorithm is not 100% correct for 
every new word. For example, if the same vowel appears more than once in 
a sentence, then it will flatten it and use it only once (e.g. `ααα` will 
be converted to `α` and so the phoneme will be `a1`). Of course, it is 
highly irregular for words like these to appear in Greek texts but it is 
not impossible. This is also the reason why I recommend you to use the 
CMU Sphinx lexicon since it already contains words like these. 

If you provide the `--path-to-lexicon` argument followed by the path to the 
`el-gr.dic` (by default it is in `./data/`) then the script will first look 
if the word is inside the lexicon and only if it is not, then it will 
convert it with this algorithm.

You may also choose to keep some specific punctuation, by using the 
`--punctuation-to-keep` argument followed by the sequence of the punctuations
(without spaces). Example: `--punctuation-to-keep .!?`.

Note: This is the main script of the package which means that you can also 
execute it from any place by calling `python -m g2p_greek <ARGUMENTS>`.


#### TL;DR
- If you want to use the CMU lexicon (significantly slower):
    `python -m g2p_greek -w /example/path/to/word.txt`  (`-w` is equivalent to `--path-to-words-txt`)
- If you want to use your own lexicon:
    `python -m g2p_greek -w /example/path/to/words.txt -l /path/to/my/lexicon.dic`
- If you want to only use this algorithm (fastest way):
    `python -m g2p_greek -u /example/path/to/words.txt` (`-u` is equivalent to `--path-to-unknown-words`)
- Default output is in `tests/output.dic`.
- To use the basic substitutions you can create a json (or csv) file like the one in `data/example_substitue_words.json`
  and use the `--substitute-words-path` (or `-s`) argument followed by the path to the file.

#### Example usage:

1. Let's say you have a `words.txt` file containing different words at 
each new line. Then you can create a file `new_lexicon.dic` which will 
contain the words followed by their phonemes.

    ```
    python -m g2p_greek --path-to-words-txt /home/user/data/words.txt \
                        --path-to-lexicon ./el-gr.dic \
                        --out-path /home/user/data/new_lexicon.dic \
                        --substitute-words-path /home/user/data/substitute_words.json
   ```
    
    The above will read each line of the `words.txt` file and for each word 
    that it finds, it will find its phonemes (either in the lexicon or by 
    the algorithm) and will create an entry to the `new_lexicon.dic`. Also, 
    if there are words in words.txt that exist in the keyset of `substitute_words.json`
    then they will be converted to the corresponding json value.
    Example output:
    
    ```
   λέξη l e1 k s i0  # calculated from el-gr.dic
   εκτός e0 k t o1 s  # calculated from our algorithm
   ααα a1 a0 a0  # calculated from el-gr.dic
   ...
   ```
   
   *IMPORTANT: the `new_lexicon.dic` will only contain the phonemes and the 
   words of the words in the `words.txt` file. It will not keep the other 
   entries from the original lexicon.*
   
2. If you have a `words.txt` file and it only contains words that <ins>do not 
exist in the lexicon</ins> then you may use the `--path-to-unknown-words` argument.
This case is useful if you have done some preprocessing to your corpus and 
you have found the out-of-vocabulary (OOV) words and you want to automatically
find their phonemes without doing it by hand. (The format of this `words.txt` should 
be the same as the one in case 1.)

    ```
   python -m g2p_greek --path-to-unknown-words /home/user/data/unknown_words.txt \
                       --out-path /home/user/data/unknown_words_lexicon.dic
   ```
    NOTE: This will run much faster than the previous one since it does not 
    load the dictionary file. On the downside, there is risk that the phonemes
    will not be that accurate. <ins>It is recommended to use the previous mode.</ins>

For more information check the `g2p_greek/g2p_greek.py` script.

---


## The `digits_to_words.py` script:
The script has its own repository [here](https://github.com/geoph9/Numbers2Words-Greek) 
but I have a similar copy here since I have done some modifications. It is **not advised** 
to use this script separately. The scripts inside the Numbers2Words-Greek repository 
are more stable.

This script contains functionality to convert numbers to their
corresponding words in Greek. It only handles positive numbers 
(you can easily change it to handle negative ones) and can also 
handle decimals. It is important to note that this algorithm does 
not take into account the gender of the noun following each number.
Also, the numbers will be converted as is and there is **no** 
post-processing like "2.5 ευρώ" -> "δυόμιση ευρώ" (the output 
will be "δύο κόμμα πέντε ευρώ").

If you only need to convert numbers to words then you may use this 
script as described below:

`python digits_to_words.py [--test-word <<WORD>>] [--path <<PATH>>] 
[--extension .lab]` 

Arguments:
- `-t` or `--test-word`: Use this only for testing. Put a word or 
number after it and check the result.

- `-p` or `--path`: Provide a path. The path can be either a directory 
or a file. 
    1. *Directory*: Inside this directory there needs to be multiple 
    text files which you want to convert. The words inside the file will 
    not be change and only the numbers will be replaced by their 
    corresponding words.
    2. *File*: If you provide a file then the same thing will happen but 
    just for this file.
- `-e` or `--extension`: Use this to change the extension of the text 
files you have provided in `--path`. This only matters if you have 
provided a directory. 

Example:

```
python digits_to_words.py --path /home/user/data/transcriptions \
                          --extension .txt
```

The above will read all the `.txt` files inside the `transcriptions` 
directory and will change the numbers to their corresponding greek words.

---


## Special cases:
1. If you have 2 dictionaries, let's say the original `el-gr.dic` and 
another one that you created from the `g2p_greek.py` script, then you 
can combine these into one script by using the `sort.py` script. For 
usage example, check the script.

2. If you have a kaldi `text` (check [here](https://kaldi-asr.org/doc/data_prep.html)
for kaldi data preparation) file then you can extract a `words.txt` file by using the following command: 
    
    `cut -d ' ' -f 2- /home/user/kaldi/egs/greek/data/train/text | sed 's/ /\n/g' | sort -u > words.txt`
    
    This will take the words that appear after the utterance ids and will separate
    them with a new line and then sort them in unique order.
    You can use the output file to create a `lexicon.txt` which is needed in kaldi.
    So, in order to extract it you may now run:
    ```
    python g2p_greek.py --path-to-words-txt /home/user/kaldi/egs/greek/data/train/words.txt \
                        --path-to-lexicon /home/user/kaldi/egs/greek/el-gr.dic \
                        --out-path /home/user/kaldi/egs/greek/data/local/lang/lexicon.txt
   ```
  
## Handling English Words

This is not as easy as it may seem. Most importantly, the phonemes that represent Greek words 
and the ones that represent English words are different (when looking at the CMU 
dictionaries). This means that we should recreate an English lexicon from scratch 
which is really hard because English words are rarely pronounced the way they are 
written. 

Currently, we are only offer a 1-1 character per character conversion, meaning that 
each latin character is mapped into on greek character. Check `english_rules.py` in 
order to see these mappings. This is really naive and, of course, does not work efficiently.
It is just a way to avoid errors and definitely not a permanent solution.

## Future Work:

1. Handle fractions in `digits_to_words`. E.g. Convert "1/10" to "ένα δέκατο".
2. Handle time input in `digits_to_words`. E.g. Convert "11:20" to "έντεκα και είκοσι"
3. Handle english characters in `g2p_greek`. E.g. For the name of the company "Facebook" -> "Φέισμπουκ f e1 i0 s b u0 k"
4. Generalize better in `g2p_greek`. Cover more special cases.
