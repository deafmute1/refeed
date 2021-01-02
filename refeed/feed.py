__author__ = 'Ethan Djeric <me@ethandjeric.com>'

#STDLIB
import shelve
from pathlib import Path
from datetime import date, datetime
from typing import Dict
import random
import string
import os
import logging

#PYPI
from mailparser.mailparser import MailParser
from mailparser.exceptions import MailParserReceivedParsingError
from feedgen.feed import FeedGenerator

# INTERNAL
from . import config

class Feed():
    """ Manage a named feed including storage, retrieval and genration functions
    """
    def __init__(self, feed_name:str) -> None:
        self.feed_name = feed_name
        self.config = config.Feed(self.feed_name)
        self.is_context_manager = False # __enter__ is called after __init__, and will overwrite this if Feed is called as a Context Manager.
        self.alternates = {}

        # Retrieve fg from shelf is it exists otherwise create it using config options
        with shelve.open(Path(__file__, '/data', 'feeds.shelf')) as shelf:
            try:
                self.fg = shelf[self.feed_name]
            except KeyError as e:
                if not self.feed_name in shelf:
                    # Mandatory
                    fg_config = self.config.info(self.feed_name)
                    self.fg = FeedGenerator()
                    self.fg.id('tag:{},{}/feeds/{}.xml'.format(fg_config['fqdn'], date.today(), feed_name))
                    self.fg.link(rel='self', type='application/atom+xml', href='{}{}/feeds/{}.xml'.format(fg_config['protocol'], fg_config['fqdn'], feed_name))
                    self.fg.title(feed_name)
                    self.fg.subtitle('Feed generated from mail messages recieved at {} by refeed'.format(self.config.account_name(self.feed_name)))
                    self.fg.author(name=fg_config['author_name'])

                    # Optional values
                    try: 
                        self.fg.logo(Path(__file__, '/static', fg_config['logo']))
                    except KeyError: 
                        pass

                    try: 
                        self.fg.language(fg_config['language'])
                    except KeyError:
                        pass
                else:
                    raise KeyError(e)

    # context manager
    def __enter__(self) -> Feed:
        self.is_context_manager = True 
        return self

    def __exit__(self) -> None: 
        _dump_shelves(self)

    def add_entry(self, mail_object:MailParser, feed_name:str) -> None:
        random.seed(None, 2)
        fe = self.fg.add_entry(order='prepend') 
        fg_config = self.config.info(self.feed_name)
        
        # id
        try:
            fe.id('tag:{},{}/feeds/{}.xml:{}'.format(fg_config['fqdn'], date.today(), feed_name, mail_object.message_id))
        except (AttributeError, MailParserReceivedParsingError): 
            fe.id('tag:{},{}/feeds/{}.xml:ID_NOT_FOUND-{}'.format(fg_config['fqdn'], date.today(), feed_name, ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))))

        # title
        try: 
            fe.title(mail_object.subject)
        except (AttributeError, MailParserReceivedParsingError):
            fe.title('SUBJECT_NOT_FOUND-{}'.format(''.join(random.choices(string.ascii_lowercase + string.digits, k=10))))
        
        # alt link and body contents
        try:
            alt_id = FeedTools.generate_unique_alt_id()
            self.alternates[alternate_id] = mail_object.body
            alt_link = '{}{}/alt-html/{}.html'.format(fg_config['protocol'], fg_config['fqdn'], alt_id)
            fe.link(rel='alternate', type='text/html', href=alt_link)
            fe.contents(content=mail_object.body, src=alt_link, type='text/html')
        except (AttributeError, MailParserReceivedParsingError):
            fe.contents(content='MAIL_BODY_NOT_FOUND', type='text/plain')

        #update time
        now = datetime.now() # entry and feed should match exactly, not be a few seconds off.
        fe.updated(now)
        self.fg.updated(now) 

    def generate_feed(self) -> None:
        # generate htmls
        for alt, body in self.alternates.items():
            with open(Path(__file__, '/alt', '{}.html'.format(str(alt))), 'w') as f:
                f.write(body)

        # generate xml
        fg.atom_file(Path(__file__, '/static', 'feeds'))

        # cleanup
        FeedTools.cleanup_alts(self.self.config.alternate_cache())

        # dump shelf data if not context manager
        if not self.is_context_manager:
            _dump_shelves()

    def _dump_shelves(self) -> None:
        with shelve.open(Path(__file__, '/data', 'feeds.shelf')) as shelf:
            shelf[self.feed_name] = self.fg

        with shelve.open(Path(__file__, '/data', 'alternate_ids.shelf')) as shelf:
            try:
                shelf[self.feed_name] = shelf[self.feed_name].extend(list(self.alternates.keys()))
            except KeyError: # feed alternates list does not exist yet
                shelf[self.feed_name] = list(self.alternates.keys())

class FeedTools():
    """ A simple, uninstanced class to contain misscellanious standalone tools related to feed mangement.
    """
    def cleanup_alts(self, feed_name:str, max:int) -> None: 
        with shelve.open(Path(__file__, '/data', 'alternates.shelf')) as shelf: 
            if not isinstance(shelf[feed_name], list):
                raise TypeError('Alternate list in shelf for feed {} is not a list'.format(feed_name))
            else: 
                if len(shelf[feed_name]) > max: 
                    delete_ids = shelf[feed_name][:(len(shelf[feed_name]) - max)]
                    deleted_ids = []
                    for alt_id in delete_ids:
                        try:
                            os.remove(Path(__file__, '/alt', '{}.html'.format()))
                            deleted_ids.append(alt_id)
                        except FileNotFoundError:
                            logging.warning('FileNotFoundError: feed.FeedTools.cleanup_alts attempted to delete {}.html and failed'.format(alt_id))
                    shelf[feed_name] = [ e for e in shelf[feed_name] if e not in deleted_ids]

    def cleanup_feeds(self) -> None:
        pass 

    def generate_unique_alt_id(self) -> str: 
        with shelve.open(Path(__file__, '/data', 'alternates.shelf')) as shelf:
            all_ids = []
            try: 
                for feed_ids in shelf.values(): 
                    if isinstance(feed_ids, list):
                        all_ids.extend(feed_ids)
            except (NameError, KeyError): # probably not necessary?
                pass

        random.seed(None, 2)
        alternate_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=30)) 
        while alternate_id in all_ids:
            alternate_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=30)) 
        return alternate_id
        
