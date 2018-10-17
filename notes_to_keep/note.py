class Note:

    def __init__(self, id, folder, title, snippet, data, att_id, att_path, acc_desc, acc_identifier, acc_username, created, edited, version, source):
        self.note_id = id
        self.folder = folder
        self.title = title
        self.snippet = snippet
        self.data = data
        self.attachment_id = att_id
        self.attachment_path = att_path
        self.account = acc_desc
        self.account_identifier = acc_identifier
        self.account_username = acc_username
        self.date_created = created
        self.date_edited = edited
        self.version = version
        self.source_file = source
        #self.folder_title_modified = folder_title_modified

if __name__ == '__main__':
    print("This is part of notes_to_keep, which cannot be called separately.")
