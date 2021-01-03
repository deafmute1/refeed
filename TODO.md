NOW:

NEXT RELEASE:
- Test, test, test
  - Implement unit tests and generate data sets for it
    - will need to use real IMAP server - send custom generated email data to it or use [?] in-the-wild data [?] 
  - Test typing with mypy
  - Determine minimum python version by testing major versions with pyenv, starting at 3.5 
- Dockerfile ... and test
- Finish docs
    - README
    - method/class docs
    - requirements.txt
- refeed.py:
- mail_to_feed.py
    - setup tasks
    - Filter returned mail from MailFetch.new_mail() to check for uniqueness against feed

FUTURE RELEASE/POTENTIAL FEATURES:
- Implement web GUI and python web server to manage config
  - flask + gunicorn (?)
- Add option to move mail that has been added to feed to arbitrary folder. 
- Add threading or async to tasker