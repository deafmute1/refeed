#Author: = 'Ethan Djeric <me@ethandjeric.com>'

#STDLIB
from typing import List, Dict, Union, Tuple, DefaultDict
from abc import ABC
import logging
from collections import defaultdict
from pathlib import Path 
import re

# 3RD PARTY
import yaml

class ConfigData():
    def __init__(self, config_path:Path): 
        logging.debug('Entering ConfigContext.__init__')
        try: 
            with config_path.open() as f:
                self.yaml = (yaml.safe_load(f))
                logging.debug('Loaded config.yaml')
        except Exception as e:
            raise UserConfigError from e
        
        default_paths = {
            "config": Path(__file__).parents[1].joinpath('run', 'config.yaml').resolve(),
            "log": Path(__file__).parents[1].joinpath('run', 'log', 'root.log').resolve(),
            "data": Path(__file__).parents[1].joinpath('run', 'data').resolve(),
            "static": Path(__file__).parents[1].joinpath('run', 'static').resolve()
        }
        self.paths = {**default_paths, **self.yaml['app']['paths']}
        self.alt_cache = yaml['app'].get('alternate_cache', 25)
        self.wait_to_update = yaml['app'].get('wait_to_update', 15)
    
    def f_names(self) -> List[str]:
        try: 
            for e in self.yaml['feeds']:
                yield str(e)
        except KeyError as e:
            logging.critical('No feed names found in config.yaml, raising UserConfigError.', exc_info=True)
            raise UserConfigError() from e

    def f_account_name(self, feed_name:str) -> Union[str, type(None)]:
        try: 
            return str(loaded_yaml['feeds'][feed_name]['account_name'])
        except KeyError as e:
            logging.error('No matching account name found for {}, raising UserConfigError'.format(feed_name), exc_info=True)
            raise UserConfigError() from e
         
    def f_folder(self, feed_name:str) -> str: 
        try: 
            return str(loaded_yaml['feeds'][feed_name]['folder'])
        except KeyError: # return default value
            logging.warning('No folder found for {}, using default value "INBOX"'.format(feed_name), exc_info=True)
            return 'INBOX'
 
    def f_filters(self, feed_name:str) -> Union[Dict[str, Dict[str, re.Pattern]], None]: 
        """ Returns filters as compiled regex patterns. 
        """
        try:
            filters = loaded_yaml['feeds'][feed_name]['filters']
        except KeyError: 
            logging.warning("No filters found in config.yaml for {}, is this correct?".format(feed_name), exc_info=True)
            return None

        ret_filters = {}
        for property_, pfilters in filters.items(): 
            if not isinstance(pfilters, dict): 
                exceptmsg = "filters from mail property {} in feed {} are not returned from yaml object as a dict: Check YAML formatting".format(property_, feed_name)
                logging.exceptiopn(exceptmsg) 
                raise UserConfigError(exceptmsg) 
            try:
                ret_filters[str(property_)] = {str(rule):re.compile(str(regex)) for (rule,regex) in pfilters.items()}  
            except re.error as e: 
                logging.exception("Invalid regex in filters for mail property: {} in feed {}".format(mailprop, feed_name))
                raise UserConfigError() from e
        return ret_filters

    def f_info(self, feed_name:str) -> Dict[str, str]:
        default_info = {
            'protocol': 'https://',
            'fqdn': 'example.com',
            'author-name': 'John Doe',
            'language': 'en',
            'logo': 'logo.png' 
        }
        try:
            yaml_info = loaded_yaml['feeds'][feed_name]['feed_info']
        except KeyError:
            logging.warning('No heading in config.yaml called feed_info found, using default values for all settings', exc_info=True)
        # From PEP448: merges two dicts using unpacking operator 
        return {**default_info, **yaml_info} 

    def f_alternate_cache(self, feed_name:str) -> int: 
        try:
            retvar = loaded_yaml['feeds'][feed_name]['alternate_cache']
        except KeyError:
            logging.info('No setting alternate cache found for feed {}, using default value 25'.format(feed_name), exc_info=True)
            return 25
 
    def a_log_level(self) -> str:
        # See https://docs.python.org/3/library/logging.html#levels
        encode_level = { 
            'critical'.casefold(): 50,
            'error'.casefold(): 40,
            'warning'.casefold(): 30,
            'info'.casefold(): 20,
            'debug'.casefold(): 10,
        }

        try:
            return encode_level[str(loaded_yaml['app']['log_level']).casefold()]
        except KeyError:
            logging.error('Either [app][log_level] is not set in config.yaml, or it is a bad value. Returning default log level (warning)')
            return 30
        except Exception: 
            return 30

    def a_wait_to_update(self) -> str:
        try:
            retvar = loaded_yaml['app']['wait_to_update']
        except KeyError: 
            logging.warning('No setting wait_to_update found for refeed, using default value 15')
            retvar = 15

        if not isinstance(retvar, int):
            logging.exception('[app][wait_to_update] value is not int')
            raise UserConfigError('[app][wait_to_update] value is not int')
        else:
            return retvar

class UserConfigError(Exception):
    """ To be raised if data returned from config.yaml does not match specifications
    """
    pass
