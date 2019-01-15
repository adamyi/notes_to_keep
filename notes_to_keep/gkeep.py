import gkeepapi
from datetime import datetime
from gkeepapi import node as g_node
from gkeepapi.exception import LoginException
from bs4 import BeautifulSoup
import logging
import sys
import re

try:
    re._pattern_type = re.Pattern
except AttributeError:
    pass


log = logging.getLogger("gkeep")

def login(gaia, pwd):
    # gkeepapi.node.DEBUG = True
    keep = gkeepapi.Keep()
    success = keep.login(gaia, pwd)
    return keep

def parseHTML(html):
    soup = BeautifulSoup(html, "html5lib")
    return soup.get_text("\n")

def generateBody(note):
    return "Imported from Apple Note\nOriginal Create Time: %s\nImport Time: %s\n-----------------------\n%s\n-----------------------\nhttps://github.com/adamyi/notes_to_keep" % (note.date_created.strftime("%c"), datetime.now().strftime("%c"), parseHTML(note.data))

def uploadNote(keep, note, header, label, pfx, folders):
    log.info("Uploading note: " + note.title)
    gnote = g_node.Note()
    if pfx is not None:
        gnote.title = "[%s] %s" % (pfx, note.title)
    else:
        gnote.title = note.title
    if header:
        gnote.text = generateBody(note)
    else:
        gnote.text = parseHTML(note.data)
    # ts = g_node.NodeTimestamps()
    # ts.load({'created': note.date_created, 'edited': note.date_edited, 'updated': datetime.now()})
    # gnote.timestamps = ts
    if label is not None:
        gnote.labels.add(label)
    if folders:
        if keep.findLabel(note.folder) is not None:
            gnote.labels.add(keep.findLabel(note.folder))
        else:
            gnote.labels.add(keep.createLabel(note.folder))
    keep.add(gnote)
    # make things slower to sync everytime instead of sync one time finally
    # however, syncing one time is more error-prone.
    # in this way, if a sync has an issue, it only affects one single note.
    keep.sync()

def createLabel(keep):
    name = "notes_to_keep %s" % datetime.now().strftime("%y/%m/%d %H:%M:%S")
    log.info("Creating label: " + name)
    label = keep.createLabel(name)
    return label

def start(gaia, pwd, notes, num, pfx, no_alter, no_label, folders):
    log.info("Logging in gaia account...")
    try:
        keep = login(gaia, pwd)
    except LoginException as e:
        log.error(e)
        log.info("If you get the \"ou must sign in on the web\" error, please check https://support.google.com/accounts/answer/2461835 to unlock your account for access without webpage (or generate an App Password if you have enabled 2SV) and try again.")
        sys.exit(1)
    log.info("Login completed.")

    if no_label:
        label = None
        log.info("Will not create a label.")
    else:
        label = createLabel(keep)

    if num != None:
        log.warning("As requested, we will only upload %s note(s)." % num)
        num = int(num)
    i = 0
    for note in notes:
        try:
            i += 1
            uploadNote(keep, note, no_alter, label, pfx, folders)
            if i == num:
                break
        except Exception as e:
            log.error(e)
            if note.title is not None:
                log.error("Error parsing/updating this note... Skip this note for now. Title: " + note.title)
            continue
    log.info("Done! Have fun~")

if __name__ == '__main__':
    print("This is part of notes_to_keep, which cannot be called separately.")
