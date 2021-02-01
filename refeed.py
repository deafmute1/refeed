#!/usr/bin/env python3
__author__ = 'Ethan Djeric <me@ethandjeric.com>'

#STDLIB 
import sys  
from pathlib import Path 

# INTERNAL
""" If we use the form `import x`, we can modify x.var. 
 However, with the form `from . import x`(relative or absolute), we cannot.
 The second form, where the namespace is modifies, it is equivalent to setting 
 the value of the import attrs to a module-specific global"""
import refeed 

def main() -> None:
    # allow user to set custom config location: 
    if len(sys.argv) > 2: 
        sys.exit("Too many arguments!")
    elif len(sys.argv) == 2:
        config_path = Path(str(sys.argv[1])).resolve() # shouldn't need str() here
        if config_path.is_file(): 
            refeed.config.paths["config"] == config_path 
        else: 
            sys.exit("Invalid path - is not a path to a file on this filesystem!")

    refeed.tasker.Run()

if __name__ == '__main__':
    main() 
