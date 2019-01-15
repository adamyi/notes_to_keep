# Notes to Keep
Export all your [Apple iCloud Notes](https://www.icloud.com/notes) on macOS to [Google Keep](https://keep.corp.google.com).

## Installation
```
pip install notes_to_keep
```

## Usage
```
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
```

## License
Copyright 2018 Adam Yi <i@adamyi.com>

[MIT License](LICENSE)

## Known Issues
This is still Alpha-quality, and is likely to have bugs. Use at your own risks. Below are some currently known issues waiting to be fixed:

* It doesn't upload any photos, attachments, etc. to Google Keep. It uploads text, and only text.
* It doesn't shorten the title, so in some extreme cases Google back-end might throw a 500 (also 500 for some other situations like certain special characters that Google doesn't support). But for most of your notes (almost all), it's gonna be just fine (2 in my 2000+ notes went wrong).

## Contribute
All submissions, including submissions by project members, require review. We use Github pull requests for this purpose.

## Disclaimer
This is not an official Google product. It is neither endorsed nor supported by either Google LLC or Apple Inc.
