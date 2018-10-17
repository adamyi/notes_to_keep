"""Packaging settings."""

from setuptools import setup
from codecs import open
from os import path
from notes_to_keep import __version__

here = path.abspath(path.dirname(__file__))
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name = 'notes_to_keep',
    version = __version__,
    description = 'Export all your Apple iCloud Notes to Google Keep',
    long_description = long_description,
    long_description_content_type = 'text/markdown',
    url = 'https://github.com/adamyi/notes_to_keep',
    author = 'Adam Yi',
    author_email = 'i@adamyi.com',
    license = 'MIT',
    classifiers = [
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'License :: OSI Approved :: MIT License',
        'Intended Audience :: End Users/Desktop',
        'Topic :: Utilities',
        'Natural Language :: English',
        'Operating System :: MacOS',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
    ],
    keywords = 'apple icloud notes google keep',
    entry_points = {
        'console_scripts': ['notes_to_keep = notes_to_keep.notes_to_keep:main']
    },
    packages = ['notes_to_keep'],
    install_requires = [
        'gkeepapi >= 0.11.2',
        'biplist >= 1.0.3',
        'beautifulsoup4 >= 4.6.0',
        'docopt >= 0.6.2',
        'html5lib >= 1.0.1'
    ],
)
