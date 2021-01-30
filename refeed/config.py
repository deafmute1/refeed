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

# Default paths 
paths = {
    "config": Path(__file__).parents[1].joinpath('run', 'config.yaml').resolve(),
    "log": Path(__file__).parents[1].joinpath('run', 'log', 'root.log').resolve(),
    "data": Path(__file__).parent[1].joinpath('run', 'data').resolve(),
    "static": Path(__file__).parent[1].joinpath('run', 'static').resolve() ,
}

paths_flag_dir = {
    "config": False,
    "log": False, 
    "data": True,
    "static": True, 
}

yaml = None 

class YAMLContainer():  
    """ Intended to be a system-wide container to the below methods/classes in this module
        in order to avoid having to pull up an instance and grab from disc in every function within refeed. 

        At run time (i.e. in tasker, between each full runthrough of the main task) init this class,
        and store the instance to config.yaml. Therefore, this can be accessed globally in refeed,
        without having to pass this instance around to each function.

    :param config_path: An absolute filesystem path to a yaml file per config.yaml.example space, using
                        pathlib.Path object.
    """
    def __init__(self, config_path:Path) -> None: 
        self.account = _PullAccount(config_path)
        self.feed = _PullFeed(config_path) 
        self.app = _PullApp(config_path)
        

class _PullConfig(ABC): 
    """ Abstract parent class to pull config from yaml files.

    :param config_path: An absolute filesystem path to a yaml file per config.yaml.example spec
    """ 
    def __init__(self, config_path:Path) -> None:
        logging.debug('Entering Config.__init__')
        try: 
            with config_path.open() as f:
                self.config = (yaml.safe_load(f))
                logging.debug('Loaded config.yaml')
        except Exception as e:
            print(e)

class _PullAccount(PullConfig):
    """ Child class of Config providing wrappers to access account section of config 

    :param config_path: An absolute filesystem path to a yaml file per config.yaml.example spec
    """
    def __init__(self, config_path:Path) -> None:
        super().__init__(config_path)
        
    def auth_type(self, account_name:str) -> str:
        return str(self.config['accounts'][account_name]['auth']['auth_type'])

    def server_options(self, account_name:str) -> Dict:
       return self.config['accounts'][account_name]['server']

    def credentials(self, account_name:str) -> Tuple[str, str]:
        user = str(self.config['accounts'][account_name]['auth']['user'])
        password = str(self.config['accounts'][account_name]['auth']['password'])
        return (user, password)

class _PullFeed(PullConfig): 
    """ Child class of Config providing wrappers to access feed section of config 

    :param config_path: An absolute filesystem path to a yaml file per config.yaml.example spec
    """
    def __init__(self, config_path:Path) -> None:
        super().__init__(config_path)

    def names(self) -> List[str]:
        try: 
            for e in self.config['feeds']:
                yield str(e)
        except KeyError as e:
            logging.critical('No feed names found in config.yaml, raising UserConfigError.', exc_info=True)
            raise UserConfigError() from e

    def account_name(self, feed_name:str) -> Union[str, type(None)]:
        try: 
            return str(self.config['feeds'][feed_name]['account_name'])
        except KeyError as e:
            logging.error('No matching account name found for {}, raising UserConfigError'.format(feed_name), exc_info=True)
            raise UserConfigError() from e
            
    def folder(self, feed_name:str) -> str: 
        try: 
            return str(self.config['feeds'][feed_name]['folder'])
        except KeyError: # return default value
            logging.warning('No folder found for {}, using default value "INBOX"'.format(feed_name), exc_info=True)
            return 'INBOX'
 
    def filters(self, feed_name:str) -> Union[Dict[str, List[re.Pattern]], None]: 
        """ Returns filters, does not check if is valid regex
        """
        try:
            filters = self.config['feeds'][feed_name]['filters']
        except KeyError: 
            logging.warning("No filters found in config.yaml for {}, is this correct?".format(feed_name), exc_info=True)
            return None

        ret_filters = {}
        for key, value in filters.items(): 
            try:
                ret_filters[str(key)] = [re.compile(str(e)) for e in value]
            except re.error as e: 
                logging.exception("Invalid regex in filters for feed: {}, header: {}".format(feed_name, key))
                raise UserConfigError() from e
            except TypeError as e:
                logging.exception("Bad type in filters for feed: {}, maybe failure to provide regex as a YAML list?".format(feed_name))
                raise UserConfigError() from e 
        return ret_filters

    def info(self, feed_name:str) -> DefaultDict[str, str]:
        try:
            # None is acccepted by default dict, but actually causes it to just behave as standard dict 
            # lamba: None will actually provide None instead of KeyError as its a callable
            return  defaultdict(lambda: None, self.config['feeds'][feed_name]['feed_info']) 
        except KeyError: # feed_info heading doesnt exist
            logging.exception('No heading in config.yaml called feed_info found, using NoneType for all settings')
            return defaultdict(lambda: None)

    def alternate_cache(self, feed_name:str) -> int: 
        try:
            retvar = self.config['feeds'][feed_name]['alternate_cache']
        except KeyError:
            logging.info('No setting alternate cache found for feed {}, using default value 25'.format(feed_name), exc_info=True)
            return 25

        if not isinstance(retvar, int):
            logging.exception('[feeds][{}][alternate_cache] value is not int'.format(feed_name))
            raise UserConfigError('[feeds][{}][alternate_cache] value is not int'.format(feed_name))
        else:
            return retvar


class _PullApp(PullConfig):
    def __init__(self, config_path:Path) -> None:
        super().__init__(config_path)

    def log_level(self) -> str:
        # See https://docs.python.org/3/library/logging.html#levels
        encode_level = { 
            'critical'.casefold(): 50,
            'error'.casefold(): 40,
            'warning'.casefold(): 30,
            'info'.casefold(): 20,
            'debug'.casefold(): 10,
        }

        try:
            return encode_level[str(self.config['app']['log_level']).casefold()]
        except KeyError:
            logging.error('Either [app][log_level] is not set in config.yaml, or it is a bad value. Returning default log level (warning)')
            return 30
        except Exception: 
            return 30

    def wait_to_update(self) -> str:
        try:
            retvar = self.config['app']['wait_to_update']
        except KeyError: 
            logging.warning('No setting wait_to_update found for refeed, using default value 15')
            retvar = 15

        if not isinstance(retvar, int):
            logging.exception('[app][wait_to_update] value is not int')
            raise UserConfigError('[app][wait_to_update] value is not int')
        else:
            return retvar

    def static_path(self) -> Path:
        return self.config['app']['static_path'] 

class UserConfigError(Exception):
    """ To be raised if data returned from config.yaml does not match specifications
    """
    pass
