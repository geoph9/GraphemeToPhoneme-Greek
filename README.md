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