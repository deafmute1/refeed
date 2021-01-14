__author__ = 'Ethan Djeric <me@ethandjeric.com>'

from refeed import tasker, global_config, config
import logging

def main():
    conf = config.App(global_config.config_path)
    # log to file
    logging.basicConfig(filename=global_config.log_path, level=conf.log_level(), filemode='a', format='%(asctime)s %(message)s')
    # log to console 
    console = logging.StreamHandler()
    logging.getLogger('').addHandler(console) # '' = root logger
    tasker.Run()

if __name__ == '__main__':
    main() 