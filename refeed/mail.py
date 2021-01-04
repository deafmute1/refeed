# Author: 'Ethan Djeric <me@ethandjeric.com>'

# std lib
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Union, Tuple
import shelve
import logging
from socket import socket as SocketError, timeout as SocketTimeout
from ssl import SSLError, CertificateError

# pypi
import mailparser
from imapclient import IMAPClient, exceptions as IMAPExceptions

#feedgen
from . import config, gconfig 

config_path = gconfig.config_path
data_path = gconfig.data_path

class MailFetch():
    """ Provides tools to fetch mail as required using _IMAPConn
    """
    @classmethod
    def new_mail(cls, feed_name:str, since:int) -> Dict[int, mailparser.MailParser]:
        """ Returns mail with 'INTERNALTIME' ('SINCE' provides only date granularity) 'SINCE' since days ago.
        
        IETF IMAP RFCs don't specify a TZ for 'INTERNALTIME'.
        """
        # open configs
        account_config = config.Account(config_path)
        feed_config = config.Feed(config_path)

        # get account info
        account_name = feed_config.account_name(feed_name)
        if account_name is None: 
            return None 
        server_options = account_config.server_options(account_name)
        auth_type = account_config.auth_type(account_name)
        credentials = account_config.credentials(account_name)

        # get feed/filter info
        filters = feed_config.filters(feed_name)
        folder = feed_config.folder(feed_name)
        logging.warning([(k,v) for k, v in server_options.items()])
        with _IMAPConn(account_name, server_options, auth_type, credentials) as server: 
            try: 
                if server.folder_exists(folder):
                    server.select_folder(folder)
                else: 
                    raise ValueError('Folder {} does not exist for account {}'.format(folder, account_name))

                try: 
                    uuids = server.search([u'SINCE', (datetime.utcnow().date() - datetime.timedelta(days=since))] , 'UTF-8')
                except IMAPExceptions.InvalidCriteriaError: 
                    logging.critical('Malformed imap search criteria, refeed will never be able to fetch new mail. Go get the author!')

                new_mail = {}
                for uuid in uuids:
                    uuid = int(uuid) # uuid is 32bit int, just cast to int in case IMAPClient is returning bytes. 
                    mail = mailparser.parse_from_bytes(server.fetch([uuid], ['FULL']))
                    for field, re_filter in filters.items():
                        try:
                            value_to_filter = getattr(mail, field)
                        except AttributeError as e:
                            raise AttributeError('filters contains a key that is not present in parsed mail object. Details: {}'.format(e))
                        if re.search(re_filter, value_to_filter) is None:
                            continue
                        else:
                            new_mail[uuid] = mail
                return new_mail

            except (SocketTimeout, SocketError): 
                logging.error('A network error with the socket library has caused mail._IMAPConn in mail.MailFetch.newmail() to fail/drop server connection for account {}'.format, exc_info=True)
            except (SSLError, CertificateError):
                logging.error('A SSL Error has caused mail._IMAPConn in mail.MailFetch.newmail() to fail/drop server connection', exc_info=True)
            except IMAPExceptions.ClientError:
                logging.error('Some otherwise unhandled imap server error has caused an error mail.MailFetch.newmail()', exc_info=True)
            except ValueError as e: 
                logging.error(e)

class _IMAPConn():
    """ Class for MailFetch which defines connection + auth to IMAP server.
    Separated from MailFetch in order to implement as a context manager, so we don't leave the server connection open for the life of MailFetch()
    """

    def __init__(self, account_name:str, server_options:Dict[str, Union[str, bool, int]], auth_type:str, credentials:Tuple[str, str]) -> None:  
        self.server_options = server_options
        self.account_name = account_name

        #connect
        try:
            self.server = IMAPClient(use_uid=True, timeout=None, **server_options)  
        except IMAPExceptions.IMAPClientError: 
            logging.exception('Failed to connect to imap account {}'.format(self.account_name))
        
        # login
        try: 
            getattr(self.server, auth_type)(*credentials)
        except (NameError): 
            logging.warning('No credentials are passed to mail._IMAPConn for imap server {}:{}, are you sure this is correct? Try checking config.yaml'.format(self.server_options['host'], self.server_options['port']))
        except (TypeError, IMAPExceptions.LoginError):
            logging.exception('Failed to authenticate to imap account {}'.format(self.account_name))

    def __enter__(self) -> IMAPClient:
        return self.server

    def __exit__(self, exc_type, exc_value, exc_traceba) -> None:
        try: 
            self.server.logout()
        except IMAPExceptions.IMAPClientError: 
            self.server.shutdown()  #try this if above fails for some reason
        except: 
            logging.warning('Failed to close connection to imap account {}'.format(self.account_name))
