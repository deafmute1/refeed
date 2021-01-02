NOW:
- Implement logging across mail, feed and config 
- Improve error handling in parrallel to logging

NEXT RELEASE:
- Test, test, test
  - Implement unit tests and generate data sets for it
    - will need to use real IMAP server - send generated email data to it or use in-the-wild data (?)
- Implement dockerfile
- Finish docs
    - README
    - method/class docs
    - requirements.txt
- refeed.py:
    - Implement some sort of scheduling paradigm
    - Implement basic web server to serve static

FUTURE RELEASE/POTENTIAL FEATURES:
- Implement web GUI to manage config
- Scramble feed_name before publishing atom.xml 