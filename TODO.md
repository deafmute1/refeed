NOW:
- Implement logging across mail, feed and config 
- Improve error handling in parrallel to logging
  - exception handlers in config.py

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
    - Implement some sort of scheduling paradigm
    - Implement basic web server to serve static
    - Write log to file
    - Filter returned mail from MailFetch.new_mail() to check for uniqueness against feed

FUTURE RELEASE/POTENTIAL FEATURES:
- Implement web GUI to manage config
- Add option to move mail that has been added to feed to arbitrary folder. 