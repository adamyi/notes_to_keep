'''
   This file was modified from mac_apt (macOS Artifact Parsing Tool).
   Changes are also subject to the terms of the MIT License.
   For the copyright information of the changes, please check the
   LICENSE file.


   Below is the original copyright information
   -------------------------------------------------------------
   Copyright (c) 2017 Yogesh Khatri 
   This file is part of mac_apt (macOS Artifact Parsing Tool).
   Usage or distribution of this software/code is subject to the 
   terms of the MIT License.
'''

#from __future__ import print_function
#from __future__ import unicode_literals # Must disable for sqlite.row_factory

import os
import datetime
import logging
from biplist import *
import binascii
import sqlite3
import zlib
import struct
from .note import Note
import json
from six import string_types

log = logging.getLogger("scannode")

def ConvertToInt(x):
    if type(x) == int:
        return x
    else:
        return int(struct.unpack('<B', x)[0])

def ReadMacAbsoluteTime(mac_abs_time): # Mac Absolute time is time epoch beginning 2001/1/1
    '''Returns datetime object, or empty string upon error'''
    if mac_abs_time not in ( 0, None, ''):
        try:
            if type(mac_abs_time) in (string_types):
                mac_abs_time = float(mac_abs_time)
            if mac_abs_time > 0xFFFFFFFF: # more than 32 bits, this should be nane-second resolution timestamp in HighSierra
                return datetime.datetime.utcfromtimestamp(mac_abs_time / 1000000000 + 978307200)
            return datetime.datetime.utcfromtimestamp(mac_abs_time + 978307200)
        except Exception as ex:
            log.error("ReadMacAbsoluteTime() Failed to convert timestamp from value " + str(mac_abs_time) + " Error was: " + str(ex))
    return ''


def ReadAttPathFromPlist(plist_blob):
    '''For NotesV2, read plist and get path'''
    try:
        plist = readPlistFromString(plist_blob)
        try:
            path = plist['$objects'][2]
            return path
        except:
            log.exception('Could not fetch attachment path from plist')
    except (InvalidPlistException, NotBinaryPlistException, Exception) as e:
        log.error ("Invalid plist in table." + str(e) )
    return ''

def GetUncompressedData(compressed):
    if compressed == None:
        return None
    data = None
    try:
        data = zlib.decompress(compressed, 15 + 32)
    except:
        log.exception('Zlib Decompression failed!')
    return data

def ReadNotesV2_V4_V6(db, notes, version, source):
    '''Reads NotesVx.storedata, where x= 2,4,6,7'''
    try:
        query = "SELECT n.Z_PK as note_id, n.ZDATECREATED as created, n.ZDATEEDITED as edited, n.ZTITLE as title, "\
                " (SELECT ZNAME from ZFOLDER where n.ZFOLDER=ZFOLDER.Z_PK) as folder, "\
                " (SELECT zf2.ZACCOUNT from ZFOLDER as zf1  LEFT JOIN ZFOLDER as zf2 on (zf1.ZPARENT=zf2.Z_PK) where n.ZFOLDER=zf1.Z_PK) as folder_parent_id, "\
                " ac.ZEMAILADDRESS as email, ac.ZACCOUNTDESCRIPTION as acc_desc, ac.ZUSERNAME as username, b.ZHTMLSTRING as data, "\
                " att.ZCONTENTID as att_id, att.ZFILEURL as file_url "\
                " FROM ZNOTE as n "\
                " LEFT JOIN ZNOTEBODY as b ON b.ZNOTE = n.Z_PK "\
                " LEFT JOIN ZATTACHMENT as att ON att.ZNOTE = n.Z_PK "\
                " LEFT JOIN ZACCOUNT as ac ON ac.Z_PK = folder_parent_id"
        db.row_factory = sqlite3.Row
        cursor = db.execute(query)
        for row in cursor:
            try:
                att_path = ''
                if row['file_url'] != None:
                    att_path = ReadAttPathFromPlist(row['file_url'])
                note = Note(row['note_id'], row['folder'], row['title'], '', row['data'], row['att_id'], att_path,
                            row['acc_desc'], row['email'], row['username'], 
                            ReadMacAbsoluteTime(row['created']), ReadMacAbsoluteTime(row['edited']),
                            version, source)
                notes.append(note)
            except:
                log.exception('Error fetching row data')
    except:
        log.exception('Query  execution failed. Query was: ' + query)

def ReadLengthField(blob):
    '''Returns a tuple (length, skip) where skip is number of bytes read'''
    length = 0
    skip = 0
    try:
        data_length = ConvertToInt(blob[0])
        length = data_length & 0x7F
        while data_length > 0x7F:
            skip += 1
            data_length = ConvertToInt(blob[skip])
            length = ((data_length & 0x7F) << (skip * 7)) + length
    except:
        log.exception('Error trying to read length field in note data blob')    
    skip += 1
    return length, skip

def ProcessNoteBodyBlob(blob):
    data = ''
    if blob == None: return data
    try:
        pos = 0
        if blob[0:3] != b'\x08\x00\x12': # header
            log.error('Unexpected bytes in header pos 0 - {:x}{:x}{:x}  Expected 080012'.format(
                ConvertToInt(blob[0]), ConvertToInt(blob[1]), ConvertToInt(blob[2])))
            return ''
        pos += 3
        length, skip = ReadLengthField(blob[pos:])
        pos += skip

        if blob[pos:pos+3] != b'\x08\x00\x10': # header 2
            log.error('Unexpected bytes in header pos {0}:{0}+3'.format(pos))
            return '' 
        pos += 3
        length, skip = ReadLengthField(blob[pos:])
        pos += skip

        # Now text data begins
        if blob[pos] != b'\x1A' and blob[pos] != 26:
            log.error(blob[pos])
            log.error('Unexpected byte in text header pos {} - byte is {:x}'.format(pos, ConvertToInt(blob[pos])))
            return ''
        pos += 1
        length, skip = ReadLengthField(blob[pos:])
        pos += skip
        # Read text tag next
        if blob[pos] != b'\x12' and blob[pos] != 18:
            log.error('Unexpected byte in pos {} - byte is {:x}'.format(pos, ConvertToInt(blob[pos])))
            return ''
        pos += 1
        length, skip = ReadLengthField(blob[pos:])
        pos += skip
        data = blob[pos : pos + length].decode('utf-8')
        # Skipping the formatting Tags
    except:
        log.exception('Error processing note data blob')
    return data

def ReadNotesHighSierra(db, notes, source):
    '''Read Notestore.sqlite'''
    try:
        query = " SELECT n.Z_PK, n.ZNOTE as note_id, n.ZDATA as data, " \
                " c3.ZFILESIZE, "\
                " c4.ZFILENAME, c4.ZIDENTIFIER as att_uuid,  "\
                " c1.ZTITLE1 as title, c1.ZSNIPPET as snippet, c1.ZIDENTIFIER as noteID, "\
                " c1.ZCREATIONDATE1 as created, c1.ZLASTVIEWEDMODIFICATIONDATE, c1.ZMODIFICATIONDATE1 as modified, "\
                " c2.ZACCOUNT3, c2.ZTITLE2 as folderName, c2.ZIDENTIFIER as folderID, "\
                " c5.ZNAME as acc_name, c5.ZIDENTIFIER as acc_identifier, c5.ZACCOUNTTYPE "\
                " FROM ZICNOTEDATA as n "\
                " LEFT JOIN ZICCLOUDSYNCINGOBJECT as c1 ON c1.ZNOTEDATA = n.Z_PK  "\
                " LEFT JOIN ZICCLOUDSYNCINGOBJECT as c2 ON c2.Z_PK = c1.ZFOLDER "\
                " LEFT JOIN ZICCLOUDSYNCINGOBJECT as c3 ON c3.ZNOTE= n.ZNOTE "\
                " LEFT JOIN ZICCLOUDSYNCINGOBJECT as c4 ON c4.ZATTACHMENT1= c3.Z_PK "\
                " LEFT JOIN ZICCLOUDSYNCINGOBJECT as c5 ON c5.Z_PK = c1.ZACCOUNT2  "\
                " ORDER BY note_id  "
        db.row_factory = sqlite3.Row
        cursor = db.execute(query)
        for row in cursor:
            try:
                att_path = ''
                if row['att_uuid'] != None:
                    att_path = os.getenv("HOME") + '/Library/Group Containers/group.com.apple.notes/Media/' + row['att_uuid'] + '/' + row['ZFILENAME']
                data = GetUncompressedData(row['data'])
                text_content = ProcessNoteBodyBlob(data)
                note = Note(row['note_id'], row['folderName'], row['title'], row['snippet'], text_content, row['att_uuid'], att_path,
                            row['acc_name'], row['acc_identifier'], '', 
                            ReadMacAbsoluteTime(row['created']), ReadMacAbsoluteTime(row['modified']),
                            'NoteStore', source)
                notes.append(note)
            except:
                log.exception('Error fetching row data')
    except:
        log.exception('Query  execution failed. Query was: ' + query)

def ReadNotes(db, notes, source):
    '''Read Notestore.sqlite'''
    cursor = db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='Z_12NOTES'")
    if cursor.fetchone() is None:
        ReadNotesHighSierra(db, notes, source)
        return
    try:
        query = " SELECT n.Z_12FOLDERS as folder_id , n.Z_9NOTES as note_id, d.ZDATA as data, " \
                " c2.ZTITLE2 as folder, c2.ZDATEFORLASTTITLEMODIFICATION as folder_title_modified, " \
                " c1.ZCREATIONDATE as created, c1.ZMODIFICATIONDATE1 as modified, c1.ZSNIPPET as snippet, c1.ZTITLE1 as title, c1.ZACCOUNT2 as acc_id, " \
                " c5.ZACCOUNTTYPE as acc_type, c5.ZIDENTIFIER as acc_identifier, c5.ZNAME as acc_name, " \
                " c3.ZMEDIA as media_id, c3.ZFILESIZE as att_filesize, c3.ZMODIFICATIONDATE as att_modified, c3.ZPREVIEWUPDATEDATE as att_previewed, c3.ZTITLE as att_title, c3.ZTYPEUTI, c3.ZIDENTIFIER as att_uuid, " \
                " c4.ZFILENAME, c4.ZIDENTIFIER as media_uuid " \
                " FROM Z_12NOTES as n " \
                " LEFT JOIN ZICNOTEDATA as d ON d.ZNOTE = n.Z_9NOTES " \
                " LEFT JOIN ZICCLOUDSYNCINGOBJECT as c1 ON c1.Z_PK = n.Z_9NOTES " \
                " LEFT JOIN ZICCLOUDSYNCINGOBJECT as c2 ON c2.Z_PK = n.Z_12FOLDERS " \
                " LEFT JOIN ZICCLOUDSYNCINGOBJECT as c3 ON c3.ZNOTE = n.Z_9NOTES " \
                " LEFT JOIN ZICCLOUDSYNCINGOBJECT as c4 ON c3.ZMEDIA = c4.Z_PK " \
                " LEFT JOIN ZICCLOUDSYNCINGOBJECT as c5 ON c5.Z_PK = c1.ZACCOUNT2 " \
                " ORDER BY note_id "
        db.row_factory = sqlite3.Row
        cursor = db.execute(query)
        for row in cursor:
            try:
                att_path = ''
                if row['media_id'] != None:
                    att_path = row['ZFILENAME']
                data = GetUncompressedData(row['data'])
                text_content = ProcessNoteBodyBlob(data)
                note = Note(row['note_id'], row['folder'], row['title'], row['snippet'], text_content, row['att_uuid'], att_path,
                            row['acc_name'], row['acc_identifier'], '', 
                            ReadMacAbsoluteTime(row['created']), ReadMacAbsoluteTime(row['modified']),
                            'NoteStore',source)
                notes.append(note)
            except:
                log.exception('Error fetching row data')
    except:
        log.exception('Query  execution failed. Query was: ' + query)

def OpenDb(inputPath):
    log.info ("Processing file " + inputPath)
    try:
        conn = sqlite3.connect(inputPath)
        log.debug ("Opened database successfully")
        return conn
    except Exception as ex:
        log.exeption ("Failed to open database, is it a valid Notes DB?")
    return None

def ProcessNotesDbFromPath(notes, source_path, version=''):
    if os.path.isfile(source_path):
        db = OpenDb(source_path)
        if db != None:
            if version:
                ReadNotesV2_V4_V6(db, notes, version, source_path)
            else:
                ReadNotes(db, notes, source_path)
            db.close()

def ScanNotes():
    '''Main Entry point function'''
    log.info("Scanning notes now")
    notes = []
    notes_v1_path = os.getenv("HOME") + '/Library/Containers/com.apple.Notes/Data/Library/Notes/NotesV1.storedata' # Mountain Lion
    notes_v2_path = os.getenv("HOME") + '/Library/Containers/com.apple.Notes/Data/Library/Notes/NotesV2.storedata' # Mavericks
    notes_v4_path = os.getenv("HOME") + '/Library/Containers/com.apple.Notes/Data/Library/Notes/NotesV4.storedata' # Yosemite
    notes_v6_path = os.getenv("HOME") + '/Library/Containers/com.apple.Notes/Data/Library/Notes/NotesV6.storedata' # Elcapitan
    notes_v7_path = os.getenv("HOME") + '/Library/Containers/com.apple.Notes/Data/Library/Notes/NotesV7.storedata' # HighSierra
    notes_path    = os.getenv("HOME") + '/Library/Group Containers/group.com.apple.notes/NoteStore.sqlite'         # Elcapitan+ has this too!

    ProcessNotesDbFromPath(notes, notes_v1_path, 'V1')
    ProcessNotesDbFromPath(notes, notes_v2_path, 'V2')
    ProcessNotesDbFromPath(notes, notes_v4_path, 'V4')
    ProcessNotesDbFromPath(notes, notes_v6_path, 'V6')
    ProcessNotesDbFromPath(notes, notes_v7_path, 'V7')
    ProcessNotesDbFromPath(notes, notes_path)

    log.info(str(len(notes)) + " note(s) found")
    return notes

if __name__ == '__main__':
    print("This is part of notes_to_keep, which cannot be called separately.")
