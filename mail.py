""" Defines classes related to mail.
"""

__author__ = 'Ethan Djeric <me@ethandjeric.com>'
__docformat__ = 'reStructuredText'

#TODO create requirements.txt - remove uneccessary packages from venv.
import imapclient
from bs4 import BeautifulSoup
from configparser import ConfigParser

class Account():
    """ Instanceable mail acccount for retrieval of new mail in a certain mailbox.

    Attributes:

    """
    def __init__(self, userid:int=None) -> None:
        pass 

    def setup(self) -> None:
        pass 

    def newMail(self) -> int:
    
    
        def fetch() -> list:
     

    def getMessagesAsHtml(self) -> None:
        pass

class Mail():
    """ 
    """