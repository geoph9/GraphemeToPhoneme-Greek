from setuptools import setup, find_packages

# Get the long description from the README file
with open('README.md', encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='g2p_greek',
    version='0.0.2',
    author='George Karakasidis',
    license='MIT',
    packages=find_packages(),
    description='Grapheme to Phoneme and Digit to Word conversion for Greek texts.',
    long_description=long_description,
    url='https://github.com/geoph9/GraphemeToPhoneme-Greek',
    keywords=['g2p', 'grapheme-to-phoneme', 'g2p_greek', 'digit to word',
              'g2p greek', 'numbers-to-words', 'number to words greek',
              'digit to word greek', 'convert digits to words in greek',
              ],
    classifiers=[
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.6+',
        'Topic :: Scientific/Engineering',
    ],
    setup_requires=['wheel'],
    include_package_data=True
)