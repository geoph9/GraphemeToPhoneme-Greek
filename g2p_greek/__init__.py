# -*- coding: UTF-8 -*-

"""
g2p-greek
~~~~~~~~~~

Grapheme to Phoneme conversion for greek.

"""

from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division
import logging

import g2p_greek.g2p_greek
import g2p_greek.digits_to_words

__title__ = 'g2p_greek'
__version__ = '0.0.1'
__author__ = 'George Karakasidis'
__email__ = 'george.karakasides@gmail.com'

log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())
