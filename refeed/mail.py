__author__ = 'Ethan Djeric <me@ethandjeric.com>'

# std lib
from typing import List, Union, TypeVar, Generic, Dict
from datetime import datetime
import re

# pypi
import mailparser
from imapclient import IMAPClient


class Account(IMAPClient):
    """ Defines an instanceable IMAPClient object for one set of user supplied settings providing both imap server specification and search filters (optional)
    """
    def __init__(self, server_options:dict, folder:str, auth:str=None, user:str=None, password:str=None, filters:Dict[str, str]=None, initial:bool=False) -> None:
        """ 
        :param server_options: A dictionary with parameters for IMAPClient in the same order as required to call 
                            See https://imapclient.readthedocs.io/en/2.1.0/api.html#imapclient-class
        :param folder: Folder on server to monitor
        :param auth: Authentification method; valid values: login, oauth, plain_login
        :param user, password: the user and password  (or ouath token) to be passed to the server
        :param filters:  A series of regex filters as dictionary values, with keys matching any item in mail ENVELOPE, including sub-items in Address fields
                        See: hhttps://imapclient.readthedocs.io/en/2.1.0/api.html#imapclient.response_types.Envelope  
        :param initial: to be set to True when this specific account+filter+folder setting combination has not been run before.
        """
        self.server = IMAPClient(**server_options)  
        try:     
            getattr(self.server, 'auth')(user, password)
        except TypeError:
            pass
        self.server.select_folder(folder)
        self.filters = filters
        self.initial = initial
   
    def mail_ids_3d(self) -> Union[List[int], None]:
        """ Returns mail UUIDs per Account() instance settings  
            Returns mail with 'INTERNALTIME' ('SINCE' provides only date granularity) greater than or equal to 3 days ago if self.initial is False.
        """
        if not self.initial:
            # IETF IMAP standards do to specify a TZ for 'INTERNALTIME', however UTC seems most likely. This is partly why 3 days instead of 1 or 2.
            criteria = [u'SINCE', (datetime.utcnow().date() - datetime.timedelta(days=2))] 
        elif self.initial:
            criteria = 'ALL'
        matching_ids = self.server.search(criteria, 'UTF-8')
        if (matching_ids is None) or (matching_ids == []): 
            return []
        return matching_ids
    
    def fetch_new_mail(self) -> List[mailparser.MailParser]:
        """ Returns mail returned by mail_ids_48hrs as a mailparser object when self.filters regex values match all its ENVELOPE data.
        """
        uuids = self.mail_ids_3d()
        retvar = []
        for uuid in uuids:
            envelope = self.server.fetch([uuid], ['ENVELOPE'])['uuid'][b'INTERNALDATE'] # discard the two layers of dictionaries
            for field, re_filter in self.filters.items():
                try:
                    value_to_filter = getattr(envelope, field)
                except AttributeError as e:
                    print ('({}): self.filter contains a key that is not present in recieved ENVELOPE object from imap server'.format(e))
                if re.search(re_filter, value_to_filter) is None:
                    break
            else:  
                retvar.append(mailparser.parse_from_bytes(self.server.fetch([uuid], ['FULL'])))
        return retvar