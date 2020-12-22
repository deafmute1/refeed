__author__ = 'Ethan Djeric <me@ethandjeric.com>'

# std lib
from typing import List, Union, TypeVar, Generic, Dict, Tuple
from datetime import datetime
import re
from pathlib import Path

# pypi
import mailparser
from imapclient import IMAPClient
import yaml
import json

class Account(IMAPClient):
    """ Defines an instanceable IMAPClient object for one set of user supplied settings providing both imap server specification
    """
    def __init__(self, server_options:dict, auth_type:str=None, login:Tuple[str, str]=None, name:str=None) -> None:
        """ 
        :param server_options: A dictionary with parameters for IMAPClient in the same order as required to call 
                            See https://imapclient.readthedocs.io/en/2.1.0/api.html#imapclient-class
        :param folder: Folder on server to monitor
        :param auth: Authentification method; valid values: login, oauth, plain_login
        :param user, password: the user and password  (or ouath token) to be passed to the server
        :param filters:  A series of regex filters as dictionary values, with keys matching any item in mail ENVELOPE, including sub-items in Address fields
                        See: https://imapclient.readthedocs.io/en/2.1.0/api.html#imapclient.response_types.Envelope  
        :param initial: to be set to True when this specific account+filter+folder setting combination has not been run before.
        """
        self.server = IMAPClient(**server_options)  
        try: 
            user, password = login
            getattr(self.server, auth_type)(user, password)
        except TypeError:
            pass
        self.name = name

    def fetch_new_mail(self, folder:str, filters:Dict[str, str]) -> List[mailparser.MailParser]:
        """ Returns mail returned by mail_ids_48hrs as a mailparser object when self.filters regex values match all its ENVELOPE data.
        """
        self.server.select_folder(folder)
        uuids = self._new_mail_ids()
        retvar = []
        for uuid in uuids:
            envelope = self.server.fetch([uuid], ['ENVELOPE'])['uuid'][b'INTERNALDATE'] # discard the two layers of dictionaries
            for field, re_filter in filters.items():
                try:
                    value_to_filter = getattr(envelope, field)
                except AttributeError as e:
                    print ('({}): self.filter contains a key that is not present in recieved ENVELOPE object from imap server'.format(e))
                if re.search(re_filter, value_to_filter) is None:
                    break
            else:  
                retvar.append(mailparser.parse_from_bytes(self.server.fetch([uuid], ['FULL'])))
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

    def _is_initial(self):
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

    def auth_type(self, account:str) -> str:
        return self.config['accounts'][account]['auth']['auth_type']

    def server_options(self, account:str) -> Dict:
       return self.config['accounts'][account]['server']

    def login(self, account:str) -> Tuple[str, str]:
        return (self.config['accounts'][account]['auth']['auth_type']['user'], self.config['accounts'][account]['auth']['auth_type']['password'])
    
