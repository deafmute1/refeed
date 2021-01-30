# Author: 'Ethan Djeric <me@ethandjeric.com>'

# std lib
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple, Union, Tuple
import shelve
import logging
from socket import error as SocketError, timeout as SocketTimeout
from ssl import SSLError, CertificateError
# pypi
import mailparser
from imapclient import IMAPClient, exceptions as IMAPExceptions
#feedgen
from . import config 

""" Please ignore the following pylint errors.
    Errors due to Pylint bugs:
       ` Value 'Union' is unsubscriptable` on typehints is a python3.9 error (PyCQA/pylint#3882)
"""

class MailFetch():

    """ Provides tools to fetch mail as required using _IMAPConn
    """

    @classmethod
    def new_mail(cls, feed_name:str, since:int) -> Union[None, Dict[int, mailparser.MailParser]]:

        """ Returns mail with 'INTERNALTIME' ('SINCE' provides only date granularity) 'SINCE' since days ago.
        
        IETF IMAP RFCs don't specify a TZ for 'INTERNALTIME'.
        """

        try: 
            # open configs
            account_config = config.Account(config.paths["config"])
            feed_config = config.Feed(config.paths["config"])
            # get account info
            account_name = feed_config.account_name(feed_name)
            server_options = account_config.server_options(account_name)
            auth_type = account_config.auth_type(account_name)
            credentials = account_config.credentials(account_name)
            # get feed/filter info
            filters = feed_config.filters(feed_name)
            folder = feed_config.folder(feed_name)
        except config.UserConfigError() as e: 
            raise ConfigError() from e 

        with _IMAPConn(account_name, server_options, auth_type, credentials) as server: 
            try: 
                if server.folder_exists(folder):
                    server.select_folder(folder)
                else: 
                    logging.exception('Folder {} does not exist for account {}'.format(folder, account_name))
                    raise ConfigError('Folder {} does not exist for account {}'.format(folder, account_name))

                try: 
                    uuids = server.search([u'SINCE', (datetime.utcnow().date() - timedelta(days=since))] , 'UTF-8')
                except IMAPExceptions.InvalidCriteriaError as e: 
                    logging.critical('Malformed imap search criteria, refeed will never be able to fetch new mail. Go get the author!', exc_info=True)
                    raise GenericHandledException() from e

                new_mail = {}
                for uuid in uuids:
                    uuid = int(uuid) # uuid is 32bit int, just cast to int in case IMAPClient is returning bytes. 
                    mail = mailparser.parse_from_bytes(server.fetch([uuid], ['RFC822'])[uuid][b'RFC822'])
                    if filters is not None: 
                        for field, re_filters in filters.items():
                            try:
                                value_to_filter = getattr(mail, field)
                            except AttributeError:
                                logging.exception('filters contains a key that is not present in parsed mail object')
                                raise ConfigError() from e

                            for filter_ in  re_filters:
                                if re.search(filter_, str(value_to_filter)) is None: 
                                    break
                            else: 
                                new_mail[uuid] = mail   

            except (SocketTimeout, SocketError) as e: 
                logging.exception('A network error with the socket library has caused mail._IMAPConn in mail.MailFetch.newmail() to fail/drop server connection for account {}'.format(account_name))
                raise GenericHandledException() from e
            except (SSLError, CertificateError):
                logging.exception('A SSL Error has caused mail._IMAPConn in mail.MailFetch.newmail() to fail/drop server connection')
                raise GenericHandledException() from e
            except IMAPExceptions.IMAPClientError as e:
                logging.exception('Some otherwise unhandled imap server error has caused an error in mail.MailFetch.newmail()')
                raise GenericHandledException() from e
            except IMAPExceptions.LoginError as e: 
                logging.exception('Failed to authenticate to imap server')
                raise GenericHandledException() from e
            except Exception as e: 
                logging.exception('Unknown error occured in mail.MailFetch.new_mail')
                raise GenericHandledException() from e

            return new_mail

class _IMAPConn():

    """ Class for MailFetch which defines connection + auth to IMAP server.
    Separated from MailFetch in order to implement as a context manager, so we don't leave the server connection open for the life of MailFetch()
    """

    def __init__(self, account_name:str, server_options:Dict[str, Union[str, bool, int]], auth_type:str, credentials:Tuple[str, str]) -> None:  
        self.server_options = server_options
        self.account_name = account_name

        #connect
        self.server = IMAPClient(use_uid=True, timeout=None, **server_options)  
        
        # login
        try: 
            getattr(self.server, auth_type)(*credentials)
        except (NameError, TypeError) as e: 
            logging.exception('No (or wrong type of) credentials were passed to mail._IMAPConn for imap server {} from config.yaml, are you sure this is correct? '.format(self.server_options['host']), exc_info=True)
            raise IMAPExceptions.LoginError() from e

    def __enter__(self) -> IMAPClient:
        return self.server

    def __exit__(self, exc_type, exc_value, exc_traceback) -> None:
        try: 
            self.server.logout()
        except IMAPExceptions.IMAPClientError: 
            self.server.shutdown()  #try this if above fails for some reason


class ConfigError(Exception):

    """ To be rasied when mail.py recieved bad data from config module, or data does not conform to mail object/imap server.

    """
    pass

class GenericHandledException(Exception):

    """ A generic exception to be raised when handling other exceptions in mail module.

    Allows tasker module to skip current job if a handled exception occurs (as opposed to simply skipping for all Exceptions.)
    """
    pass
