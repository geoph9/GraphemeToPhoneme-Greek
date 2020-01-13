# Grapheme To Phoneme Conversion For Greek

This repository contains code for converting words to their
corresponding phonemes. In addition, there is functionality
to convert numbers to words (e.g. 10 -> δέκα) up until 
`10^13 - 1` (1 trillion minus one).

The conversion from words to phonemes is done in 3 stages.
1. Convert single characters to their corresponding phonemes
2. Locate diphthongs and replace the previous content
3. Sanity check to make sure that no consecutive phonemes appear 
and that there is at least one intonated phoneme in each word.

The full pipeline with lexicon lookup is:
1. Load lexicon into a dictionary. The dictionary will actually 
be a hash table where the keys are the `N` first characters of 
each word and the value will be another dictionary containing 
the words as keys and the phonemes as values.
E.g. `{ "αυτ": {"αυτός": "a0 f t o1 s", "αυτοί": "a0 f t i1", ...}, ... }`

2. Open the file containing the unknown words.
3. For each word look it up in the dictionary
4. If it exists then return the dictionary entry
5. Otherwise, return convert using our algorithm

A description of the algorithm can be found in `g2p_own_rules.py`.