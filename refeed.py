__author__ = 'Ethan Djeric <me@ethandjeric.com>'

from refeed import tasker, config
import logging

def main():
    conf = config.App(config.paths["config"])
    # log to file
    logging.basicConfig(filename=str(config.paths["log"]), level=conf.log_level(), filemode='a', format='%(asctime)s %(message)s')
    # log to console 
    console = logging.StreamHandler()
    logging.getLogger('').addHandler(console) # '' = root logger
    tasker.Run()

if __name__ == '__main__':
    main() 
