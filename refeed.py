__author__ = 'Ethan Djeric <me@ethandjeric.com>'

# std lib
import time
import logging
from pathlib import Path
# pypi

# refeed
from .refeed import tasker, config

def main():
    # log to file
    loglevel = getattr(logging, config.App().log_level())
    logging.basicConfig(filename=Path(__file__).joinpath('refeed', 'log', 'root.log'), level=loglevel, filemode='a')
    # log to console as well
    console = logging.StreamHandler()
    logging.getLogger('').addHandler(console) # '' = root logger
    tasker.Run() 

if __name__ == '__main__':
    main()