__author__ = 'Ethan Djeric <me@ethandjeric.com>'

#STDLIB
from typing import List, Dict, DefaultDict, Union
from abc import ABC
from collections import defaultdict
import logging
from pathlib import Path, PurePath # PurePath is most base class of pathlib objects

#PYPI
import yaml


class Config(ABC): 
    """ Abstract parent class to pull config from yaml files.

    :param config_path: An absolute filesystem path to a yaml file per config.yaml.example spec
    """ 
    def __init__(self, config_path:PurePath) -> None:
        try: 
            with open(config_path) as f:
                self.config = (yaml.safe_load(f))


class Account(Config): 
    """ Child class of Config providing wrappers to access account section of config 

    :param config_path: An absolute filesystem path to a yaml file per config.yaml.example spec
    """
    def __init__(self, config_path:PurePath=Path(__file__).joinpath('/config', 'config.yaml')) -> None:
        super().__init__(config_path)
        
    def auth_type(self, account_name:str) -> str:
        return str(self.config['accounts'][account_name]['auth']['auth_type'])

    def server_options(self, account_name:str) -> Dict:
       return self.config['accounts'][account_name]['server']

    def credentials(self, account_name:str) -> Tuple[str, str]:
        user = str(self.config['accounts'][account_name]['auth']['auth_type']['user'])
        password = str(self.config['accounts'][account_name]['auth']['auth_type']['password'])
        return (user, password)

class Feed(Config): 
    """ Child class of Config providing wrappers to access feed section of config 

    :param config_path: An absolute filesystem path to a yaml file per config.yaml.example spec
    """
    def __init__(self, config_path:PurePath=Path(__file__).joinpath('/config', 'config.yaml')) -> None:
        super().__init__(config_path)

    def names(self) -> List[str]:
        try: 
            for e in self.config['feeds']:
                yield e

    def account_name(self, feed_name:str) -> str:
            return str(self.config['feeds'][feed_name]['account_name'])

    def folder(self, feed_name:str) -> str: 
        try: 
            return str(self.config['feeds'][feed_name]['folder'])
        except KeyError: # return default value
            logging.error('No folder found for {}, using default value "INBOX"'.format(feed_name))
            return 'INBOX'
 
    def filters(self, feed_name:str) -> Dict[str, str]: 
        return self.config['feeds'][feed_name]['filters']
    
    def info(self, feed_name:str) -> DefaultDict[Union[[str, None]]]:
        try:
            return defaultdict(None, self.config['feeds'][feed_name]['feed_info'])
        except KeyError: # feed_info heading doesnt exist
            logging.warning('No heading in config.yaml called feed_info found, using NoneType for all settings')
            return defaultdict(None)

    def alternate_cache(self, feed_name:str) -> int: 
        try:
            return int(self.config['feeds'][feed_name]['alternate_cache'])
        except KeyError:
            logging.info('No setting alternate cache found for feed {}, using deafult value 25'.format(feed_name))
            return 25

class App(Config):
    def __init__(self, config_path:PurePath=Path(__file__).joinpath('/config', 'config.yaml')) -> None:
        super().__init__(config_path)

    def log_level(self) -> str:
        try:
            return str(self.config['app']['log_level'])
        except KeyError: 
            logging.info('No setting log_level found for refeed, using default value WARNING')
            return 'WARNING'

    def wait_to_update(self) -> str:
        try:
            return int(self.config['app']['wait_to_update'])
        except KeyError: 
            logging.info('No setting wait_to_update found for refeed, using default value 15')
            return 15
            
