__author__ = 'Ethan Djeric <me@ethandjeric.com>'

# std lib
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Generic, List, Tuple, TypeVar, Union

# pypi
import mailparser
import yaml
from imapclient import IMAPClient


class Account():
    """ Defines an instanceable IMAPClient object for one set of user supplied settings providing both imap server specification
    """
    def __init__(self, server_options:dict, auth_type:str=None, login:Tuple[str, str]=None, name:str=None) -> None:
        """ 
        :param server_options: A dictionary with parameters for IMAPClient in the same order as required to call 
                            See https://imapclient.readthedocs.io/en/2.1.0/api.html#imapclient-class
        :param folder: Folder on server to monitor
        :param auth: Authentification method; valid values: login, oauth, plain_login
        :param login: a tuple as per (user, password) for the auth method
        :param name: the name of the account, as per yaml configuration
        """
        self.server = IMAPClient(**server_options)  
        try: 
            user, password = login
            getattr(self.server, auth_type)(user, password)
        except TypeError:
            pass
        self.name = name

    def fetch_new_mail(self, folder:str, filters:Dict[str, str]) -> List[mailparser.MailParser]:
        """ Returns mail returned by _new_mail_ids as a mailparser object when filters regex values match all its ENVELOPE data.

        :param folder: Folder on server to monitor
        :param filters:  A series of regex filters as dictionary values, with keys matching any item in mail ENVELOPE, including sub-items in Address fields
                        See: https://imapclient.readthedocs.io/en/2.1.0/api.html#imapclient.response_types.Envelope  
        """
        self.server.select_folder(folder)
        uuids = self._new_mail_ids()
        retvar = []
        for uuid in uuids:
            mail = mailparser.parse_from_bytes(self.server.fetch([uuid], ['FULL']))
            for field, re_filter in filters.items():
                try:
                    value_to_filter = getattr(mail, field)
                except AttributeError as e:
                    print ('({}): self.filter contains a key that is not present in parsed mail object'.format(e))
                if re.search(re_filter, value_to_filter) is None:
                    break
            else:  
                retvar.append(mail)
        return retvar

    def _new_mail_ids(self, folder) -> Union[List[int], None]:
        """ Returns mail UUIDs per Account() instance settings  
            Returns mail with 'INTERNALTIME' ('SINCE' provides only date granularity) greater than or equal to 3 days ago if self.initial is False.
        """
        if self._is_inital():
            criteria = 'ALL'
        elif not self._is_inital():
            # IETF IMAP standards do to specify a TZ for 'INTERNALTIME', however UTC seems most likely. This is partly why 3 days instead of 1 or 2.
            criteria = [u'SINCE', (datetime.utcnow().date() - datetime.timedelta(days=2))] 
            self._store_not_initial()
        matching_ids = self.server.search(criteria, 'UTF-8')
        if (matching_ids is None) or (matching_ids == []): 
            return []
        return matching_ids

    def _is_initial(self) -> bool:
        with open(Path(__file__).joinpath('data', 'initialised.json', 'r')) as rf:
            initialised = json.load(rf)
        try:
            return initialised[self.name]
        except KeyError: 
            return False

    def _store_not_initial(self):
        with open(Path(__file__).joinpath('data', 'initialised.json'), 'r') as rf:
            initialised = json.load(rf)
        initalised[self.name] = False
        with open(Path(__file__).joinpath('data', 'initialised.json'), 'w') as wf:
            json.dump(initialised)

class Config(): 
    """ Pull config from yaml files, and provide wrappers to prepare for Account() needs
    """ 
    def __init__(self, config_path:str) -> None:
        with open(config_path) as f:
            self.config = (yaml.safe_load(f))
        self.accounts = []
        for account in self.config['accounts']:        
            self.accounts.append(account)

    def auth_type(self, name:str) -> str:
        return self.config['accounts'][name]['auth']['auth_type']

    def server_options(self, name:str) -> Dict:
       return self.config['accounts'][name]['server']

    def login(self, name:str) -> Tuple[str, str]:
        return (self.config['accounts'][name]['auth']['auth_type']['user'], self.config['accounts'][name]['auth']['auth_type']['password'])
    
    def folder(self, name:str) -> str: 
        return self.config['rules'][name]['folder']
    
    def filters(self, name:str) -> Dict[str, str]: 
        return self.config['rules'][name]['filters']
