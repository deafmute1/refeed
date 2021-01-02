__author__ = 'Ethan Djeric <me@ethandjeric.com>'

# std lib
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Generic, List, Tuple, TypeVar, Union
import shelve

# pypi
import mailparser
from imapclient import IMAPClient

#from feedgen
from . import config

class MailFeed():
    """ Defines an instanceable IMAPClient object for one set of user supplied settings providing both imap server specification
    """
    def __init__(self, feed_name:str) -> None:
        self.feed_name = feed_name
        self.account_config = config.Account(Path(__file__, '/config', 'config.yaml'))
        self.feed_config = config.Feed(Path(__file__, '/config', 'config.yaml'))

        account_name = self.feed_config.account_name(self.feed_name)
        self.server = IMAPClient(**self.account_config.server_options(account_name))  
        try: 
            user, password = self.account_config.login(account_name)
            getattr(self.server, self.account_config.auth_type())(user, password)
        except TypeError:
            pass

    def fetch_new_mail(self) -> List[mailparser.MailParser]:
        """ Returns mail returned by _new_mail_ids as a mailparser object when filters regex values match its mail fields

        :param folder: Folder on server to monitor
        :param filters:  A series of regex filters as dictionary values, with keys matching any item in mail ENVELOPE, including sub-items in Address fields
                        See: https://imapclient.readthedocs.io/en/2.1.0/api.html#imapclient.response_types.Envelope  
        """
        self.server.select_folder(self.feed_config.folder(self.feed_name))
        uuids = self._new_mail_ids()
        filters = self.feed_config.filters(self.feed_name)
        retvar = []
        for uuid in uuids:
            mail = mailparser.parse_from_bytes(self.server.fetch([uuid], ['FULL']))
            for field, re_filter in filters.items():
                try:
                    value_to_filter = getattr(mail, field)
                except AttributeError as e:
                    raise AttributeError('filters contains a key that is not present in parsed mail object. Details: {}'.format(e))
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
            # IETF IMAP standards do not specify a TZ for 'INTERNALTIME', however UTC seems most likely. This is partly why 3 days instead of 1 or 2.
            criteria = [u'SINCE', (datetime.utcnow().date() - datetime.timedelta(days=2))] 
            self._store_not_initial()
        matching_ids = self.server.search(criteria, 'UTF-8')
        if (matching_ids is None) or (matching_ids == []): 
            return []
        return matching_ids


    def _is_inital(self) -> bool:
        with shelve.open(Path(__file__, '/data', 'init.shelf')) as shelf:
            try:
                return shelf[self.feed_name]
            except KeyError:
                if not (self.feed_name in shelf):
                    return False
                else: 
                    raise KeyError()
        
    def _store_not_initial(self) -> None:
        with shelve.open(Path(__file__, '/data', 'init.shelf')) as shelf: 
            shelf[self.feed_name] = False