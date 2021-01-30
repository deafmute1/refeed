__author__ = 'Ethan Djeric <me@ethandjeric.com>'

<<<<<<< HEAD
#STDLIB 
import logging 
from sys import argv, exit 
from pathlib import Path 

# INTERNAL
""" If we use the form `import x`, we can modify x.var. 
 However, with the form `from . import x`(relative or absolute), we cannot.
 The second form, where the namespace is modifies, it is equivalent to setting 
 the value of the import attrs to a module-specific global"""
import refeed 

def main():
    # allow user to set custom config location: 
    if len(argv) > 2: 
        exit("Too many arguments!")
    elif len(argv) == 2:
        config_path = Path(str(argv[1])).resolve() # shouldn't need str() here
        if config_path.is_file(): 
            refeed.config.paths["config"] == config_path 
        else: 
            exit("Invalid path - is not a path to a file on this filesystem!")

    conf = refeed.config.App(config.paths["config"])
    # log to file
    logging.basicConfig(filename=str(refeed.config.paths["log"]), level=conf.log_level(), filemode='a', format='%(asctime)s %(message)s')
    refeed.tasker.Run()

if __name__ == '__main__':
    main() 
=======
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
>>>>>>> e5d1f817b9c100063a6da15ad48f7673757bf99a
