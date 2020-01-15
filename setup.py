# -*- coding: utf-8 -*-

import os
from os import path

from setuptools import setup
# from distutils.core import setup


here = path.abspath(path.dirname(__file__))
# Get the long description from the README file
with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='g2p-greek',
    version='0.0.1',
    author='George Karakasidis',
    author_email='george.karakasides@gmail.com',
    license='MIT',
    packages=['g2p-greek'],
    description='Grapheme to Phoneme conversion for greek.',
    long_description=long_description,
    url='https://github.com/geoph9/GraphemeToPhoneme-Greek',
    keywords=['g2p', 'grapheme-to-phoneme', 'g2p_greek',
              'g2p greek', 'numbers-to-words', 'number to words greek'],
    classifiers=[
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: Healthcare Industry',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.6.9',
        'Topic :: Scientific/Engineering',
        'Topic :: Scientific/Engineering :: Chemistry',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    include_package_data=True
)