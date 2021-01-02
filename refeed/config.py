__author__ = 'Ethan Djeric <me@ethandjeric.com>'

#STDLIB
from typing import List, Dict
from abc import ABC

#PYPI
import yaml

class Config(ABC): 
    """ Abstract parent class to pull config from yaml files.

    :param config_path: An absolute filesystem path to a yaml file per config.yaml.example spec
    """ 
    def __init__(self, config_path:str) -> None:
        try: 
            with open(config_path) as f:
                self.config = (yaml.safe_load(f))
        except FileNotFoundError as e: 
            raise FileNotFoundError('yaml config not found. More {}'.format(e))


class Account(Config): 
    """ Child class of Config providing wrappers to access account section of config 

    :param config_path: An absolute filesystem path to a yaml file per config.yaml.example spec
    """
    def __init__(self, config_path:str) -> None:
        super().__init__(config_path)
        
    def auth_type(self, account_name:str) -> str:
        return self.config['accounts'][account_name]['auth']['auth_type']

    def server_options(self, account_name:str) -> Dict:
       return self.config['accounts'][account_name]['server']

    def login(self, account_name:str) -> Tuple[str, str]:
        return (self.config['accounts'][account_name]['auth']['auth_type']['user'], self.config['accounts'][account_name]['auth']['auth_type']['password'])



class Feed(Config): 
    """ Child class of Config providing wrappers to access feed section of config 

    :param config_path: An absolute filesystem path to a yaml file per config.yaml.example spec
    """
    def __init__(self, config_path:str):
        super().__init__(config_path)

    def feed_names(self) -> List[str]:
        try: 
            for e in self.config['feeds']:
                yield e
        except KeyError as e:
            raise KeyError('Incorect syntax in or non-existent rule section. More {}'.format(e))

    def account_name(self, feed_name:str) -> str:
        return self.config['feeds'][feed_name]['account_name']

    def folder(self, feed_name:str) -> str: 
        return self.config['feeds'][feed_name]['folder']
 
    def filters(self, feed_name:str) -> Dict[str, str]: 
        return self.config['feeds'][feed_name]['filters']
    
    def info(self, feed_name:str) -> Dict[str, str]:
        return self.config['feeds'][feed_name]['feed_info']

    def alternate_cache(self, feed_name:str) -> int: 
        return int(self.config['feeds'][feed_name]['alternate_cache'])