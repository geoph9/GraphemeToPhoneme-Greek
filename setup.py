# -*- coding: utf-8 -*-

import os
from setuptools import setup
# from distutils.core import setup

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup(
    name='g2p-greek',
    version='0.0.1',
    author='G.Kara',
    # author_email='B.Gees@gmail.com',
    license='MIT',
    packages=['g2p-greek'],
    description='Grapheme to Phoneme conversion for greek.',
    long_description='my package long description',
    keywords='g2p grapheme-to-phoneme g2p_greek numbers-to-words',
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
    install_requires=requirements,
    zip_safe=False
)