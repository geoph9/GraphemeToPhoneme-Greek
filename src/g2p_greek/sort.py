#!/usr/bin/env python3
# Kyle Gorman <gormanky@ohsu.edu>
# The UNIX `sort` utility does not always sort the dictionary the way that
# HTK expects; this one does

# Taken from the Prosodylab-Aligner repository https://github.com/prosodylab/Prosodylab-Aligner


import fileinput


def main():
    """ Usage:
            python sort.py unknown_words_lexicon.dic ./el-gr.dic > complete_lexicon.dic
        The two lines above will combine the two lexicons and will sort them into a complete lexicon

        If you want to replace the file el-gr.dic then:
            python sort.py unknown_words_lexicon.dic ./el-gr.dic > tmp
            mv tmp ./el-gr.dic
    """
    lines = frozenset(l.rstrip() for l in fileinput.input(openhook=fileinput.hook_encoded("utf-8")))  # accumulate
    print("\n".join(sorted(lines)))                           # linearize


if __name__ == "__main__":
    main()
