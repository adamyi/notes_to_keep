#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""notes_to_keep - export all your Apple Notes to Google Keep

Usage:
    notes_to_keep <email> <password> [options]
    notes_to_keep --help
    notes_to_keep --version

Arguments:
    <email>           Your Google account
    <password>        The password of your Google account

Options:
    --num=<num>       The number of notes to be exported to Google
                      Keep (default: all notes will be exported)
    --prefix=<pfx>    Append a prefix before the title of all notes.
                      A pair of [] will be put around it
                      automatically. (Default: empty)
    --meta-header     Add a header message to the beginning of each
                      note to include the original creation time
                      of the note and the import time.
    --no-label        Do not create a label for all imported notes.
                      By default, we will create a new label for
                      all imported notes.
    --folders         Create labels that correspond to the folders
                      in your Notes db.
"""

import logging
from docopt import docopt
from .scan_notes import ScanNotes
from . import gkeep
from . import __version__

log = logging.getLogger("main")
logging.basicConfig(format='%(asctime)s: %(levelname)s: %(name)s (%(lineno)s): %(message)s')
logging.root.setLevel(level=logging.INFO)

def start(args):
    gaia = args['<email>']
    password = args['<password>']
    num = args['--num']
    pfx = args['--prefix']
    header = args['--meta-header']
    no_label = args['--no-label']
    folders = args['--folders']

    notes = ScanNotes()
    gkeep.start(gaia, password, notes, num, pfx, header, no_label, folders)

def main():
    args = docopt(__doc__, version=__version__)
    start(args)


if __name__ == '__main__':
    main()
