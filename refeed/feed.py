# Author: 'Ethan Djeric <me@ethandjeric.com>'

#STDLIB
from __future__ import annotations # allow referecning Feed as a type from within Feed for __enter__
import shelve
from pathlib import Path
from datetime import date, datetime
from typing import Tuple, Dict
import random
import string
import logging

# 3RD PARTY 
from mailparser import MailParser
from mailparser.exceptions import MailParserReceivedParsingError
from feedgen.feed import FeedGenerator
<<<<<<< HEAD

# INTERNAL
""" If we use the form `import x`, we can modify x.var. 
 However, with the form `from . import x`(relative or absolute), we cannot.
 The second form, where the namespace is modifies, it is equivalent to setting 
 the value of the import attrs to a module-specific global"""
import config
=======
# INTERNAL
#pylint tells you not to do this, but it is correct
from . import config, global_config 

config_path = global_config.config_path
data_path = global_config.data_path
static_path = global_config.static_path
>>>>>>> e5d1f817b9c100063a6da15ad48f7673757bf99a

class Feed():
    """ Instanceable class to manage a named feed including storage, retrieval and genration functions.

    :param feed_name: a string containg a feed name present in config.Feed.names() 
    """
    def __init__(self, feed_name:str) -> None:
        self.feed_name = feed_name
        self.config = config.Feed(config.paths["config"])
        self.alternates = {}
        self.added_mail_uuids = []
        self.written_mail_uuids = None

        # Retrieve fg from shelf is it exists otherwise create it using config options
        with shelve.open(str(Path(config.paths["data"]).joinpath('feeds.shelf'))) as shelf:
            try:
                self.fg = shelf[self.feed_name]
            except KeyError as e:
                if not self.feed_name in shelf:
                    # Mandatory
                    fg_config = self.config.info(self.feed_name)
                    self.fg = FeedGenerator()
                    self.fg.id('tag:{},{}/feeds/{}.xml'.format(fg_config['fqdn'], date.today(), feed_name))
                    href_ = '{}{}/feeds/{}.xml'.format(fg_config['protocol'], fg_config['fqdn'], feed_name)
                    self.fg.link(rel='self', type='application/atom+xml', href=href_)
                    self.fg.title(feed_name)
                    self.fg.subtitle('Feed generated from mail messages recieved at {} by refeed'.format(self.config.account_name(self.feed_name)))
                    self.fg.author(name=fg_config.get('author_name', 'Example Name'))

                    # Optional values
                    try: 
                        self.fg.logo(str(Path(config.paths["static"]).joinpath(fg_config['logo'])))
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
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback) -> None: 
        self._dump_shelves()

    def add_entries_from_dict_if_new(self, mails:Dict[int, MailParser]) -> bool:
        try: 
            for uuid, mail in mails:
                if FeedTools.uuid_not_in_feed(self.feed_name, uuid):
                    self.add_entry((uuid, mail))
        except (TypeError, ValueError): 
            logging.error('Given NoneType as mailobject to Feed, some error in mail with IMAP.', exc_info=True)
        except Exception: 
            logging.error('Unexpected error', exc_info=True)

    def add_entry(self, mail:Tuple[int, MailParser]) -> None:
        random.seed(None, 2)
        fe = self.fg.add_entry(order='prepend') 
        fg_config = self.config.info(self.feed_name)
        
        # id
        try:
            fe.id('tag:{},{}/feeds/{}.xml:{}'.format(fg_config['fqdn'], date.today(), self.feed_name,mail[0]))
        except (AttributeError, MailParserReceivedParsingError): 
            fe.id('tag:{},{}/feeds/{}.xml:ID_NOT_FOUND-{}'.format(fg_config['fqdn'], date.today(), self.feed_name, ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))))

        # title
        try: 
            fe.title(mail[1].subject)
        except (AttributeError, MailParserReceivedParsingError):
            fe.title('SUBJECT_NOT_FOUND-{}'.format(''.join(random.choices(string.ascii_lowercase + string.digits, k=10))))
        
        # alt link and body contents
        try:
            alt_id = FeedTools.generate_unique_alt_id()
            self.alternates[alt_id] = mail[1].body
            alt_link = '{}{}/alt-html/{}.html'.format(fg_config['protocol'], fg_config['fqdn'], alt_id)
            fe.link(rel='alternate', type='text/html', href=alt_link)
            fe.contents(content=mail[1].body, src=alt_link, type='text/html')
        except (AttributeError, MailParserReceivedParsingError):
            fe.contents(content='MAIL_BODY_NOT_FOUND', type='text/plain')

        #update time
        now = datetime.now() # entry and feed should match exactly, not be a few seconds off.
        fe.updated(now)
        self.fg.updated(now) 

        # cache uuids added to feed
        self.added_mail_uuids.append(mail[0]) 

    def generate_feed(self) -> None:
        # generate htmls
        if self.alternates != {}:
            try: 
                for alt_id, body in self.alternates.items():
<<<<<<< HEAD
                    with Path(config.paths["static"]).joinpath('alt', '{}.html'.format(str(alt_id))).open(mode='w') as f:
=======
                    with open(Path(static_path).joinpath('alt', '{}.html'.format(str(alt_id))), 'w') as f:
>>>>>>> e5d1f817b9c100063a6da15ad48f7673757bf99a
                        f.write(body)
            except Exception: # Exception gets *most* inbuilt exceptions, except KeyboardInterrupt, SystemInterrupt and some others which are out of scope
                logging.error('Failed to write some html alt pages to file for new entries for feed {}'.format(self.feed_name), exc_info=True)
            finally:
                logging.info('Successfully generated html alt pages: {} for feed {}'.format(list(self.alternates.keys()), self.feed_name))
                FeedTools.cleanup_alts(self.feed_name, self.config.alternate_cache(self.feed_name))

        # generate xml
        try: 
           self.fg.atom_file(str(Path(config.paths["static"]).joinpath('feed', '{}.xml'.format(self.feed_name))))
        except Exception: # TODO: Find out what fucking exceptions that feedgen actually raises, if any(not documented - check source)
            logging.error('Failed to generate and write new copy of feed {} to file'.format(self.feed_name))
        finally: 
            self.written_mail_uuids = self.added_mail_uuids

    def _dump_shelves(self) -> None:
        with shelve.open(str(Path(config.paths["data"]).joinpath('feeds.shelf'))) as shelf:
            shelf[self.feed_name] = self.fg
            logging.info('Atom data for feed {} stored to disk'.format(self.feed_name))
        
        with shelve.open(str(Path(config.paths["data"]).joinpath('alternate_ids.shelf'))) as shelf:
            try:
                shelf[self.feed_name] = shelf[self.feed_name].extend(list(self.alternates.keys()))
            except (KeyError, AttributeError): # feed alternates list does not exist yet
                shelf[self.feed_name] = list(self.alternates.keys())
                logging.info('Alt id data for feed {} stored to disk for first time'.format(self.feed_name))
            finally: 
                logging.info('Alt id data for feed {} stored back to disk'.format(self.feed_name))

        with shelve.open(str(Path(config.paths["data"]).joinpath('mail_uuids.shelf'))) as shelf:
            try: 
                shelf[self.feed_name] = shelf[self.feed_name].extend(self.written_mail_uuids)
            except (KeyError, AttributeError): # feed id list does not exist yet
                shelf[self.feed_name] = self.written_mail_uuids
                logging.info('Mail UUID data for feed {} stored to disk for first time'.format(self.feed_name))
            except TypeError: 
                if self.written_mail_uuids is None:
                    logging.info('Failed to write mail UUIDs to shelf file for feed {}: Newly written mail UUID data is None. Feed._dump_shelves() was likely called without any new items beeing added to feed'.format(self.feed_name), exc_info=True)
                else: 
                    logging.error('Failed to write mail UUIDs to shelf file for feed {}: Newly written mail UUID is not None, some unexpected error has occured. '.format(self.feed_name), exc_info=True)
            finally: 
                logging.info('Mail UUID data for feed {} stored back to disk'.format(self.feed_name))                


class FeedTools():
    """ A uninstanced class to contain misscellanious standalone class methods for feed mangement.
    """
    @classmethod
    def uuid_not_in_feed(cls, feed_name:str, uuid:int):
        with shelve.open(str(Path(config.paths["data"]).joinpath('mail_uuids.shelf'))) as shelf:
            try:
                for uuids in shelf[feed_name]: 
                    if uuid not in uuids: 
                        return True
                    else: 
                        return False
            except KeyError: # presume that this is first mail and no data is stored for feed
                logging.warning('Could not find feed_name in mail_uuid.shelf when checking if mail uuid is in feed - this is a normal occurance if the feed has no mail entries in it yet. Returning True: uuid is not in feed yet')
                return True
                

    @classmethod
    def cleanup_alts(cls, feed_name:str, max_alts:int) -> None: 
        with shelve.open(str((Path(config.paths["data"]).joinpath('alternates.shelf')))) as shelf: 
            if not isinstance(shelf[feed_name], list):
                raise TypeError('Alternate list in shelf for feed {} is not a list'.format(feed_name))
            else: 
                if len(shelf[feed_name]) > max_alts: 
                    delete_ids = shelf[feed_name][:(len(shelf[feed_name]) - max_alts)]
                    deleted_ids = []
                    for alt_id in delete_ids:
                        try:
                            Path(config.paths["static"]).joinpath('alt', '{}.html'.format(alt_id)).unlink()
                        except FileNotFoundError:
                            logging.error('feed.FeedTools.cleanup_alts attempted to delete static/{}.html and failed'.format(alt_id), exc_info=True) 
                        finally: 
                            deleted_ids.append(alt_id) 
                    shelf[feed_name] = [e for e in shelf[feed_name] if e not in deleted_ids] 

    @classmethod
    def cleanup_feeds(cls) -> None:
        """ Remove a feed completely from all data stores if not present in config.yaml.
        
        This includes:
            - the fg object in feeds.shelf
            - the atom feed itself, in /static/feed
            - the alternate ids in alternate_ids.shelf
            - the alternate html pages themselves, in /static/alt
            - the recieved mail uuids in mail_uuids.shelf

        This is a highly expensive operation, especially since where possible it does not assume all of the above data sources are in agreement with each other and instead checks each source against the config.
        It is intended to be run only when the refeed is started.
        """
        conf = config.Feed(config.paths["config"]) 

        # remove fg object, atom feed xml
        with shelve.open(str(Path(config.paths["data"]).joinpath('feeds.shelf'))) as shelf:
            del_feeds = []
            for feed in shelf.keys(): 
                if feed not in conf.names():
                    del_feeds.append(feed)  # we should not remove objects from shelf as we iterate over it
            try:
                for feed in del_feeds:
                    del shelf[feed]
            except KeyError:
                logging.error('Failed to remove feed and fg item for no longer defined feed from feeds.shelf: {}'.format(feed), exc_info=True )

                
        # remove atom feed xml 
        for file in Path(config.paths["static"]).joinpath('feed').iterdir(): 
            if file.is_file():
                try:
                    Path(config.paths["static"]).joinpath('feed', '{}'.format(file)).unlink()
                except FileNotFoundError: 
                    logging.error('Failed to remove feed xml file for no longer defined feed from /static/feed: {}'.format(file), exc_info=True)
        
        # remove alt ids and pages - this is the only place we do not check each item against config as alt page names are only matched to feed names by alternate_ids.shelf
        with shelve.open(str(Path(config.paths["data"]).joinpath('alternate_ids.shelf'))) as shelf:
            del_feeds = []
            for feed, ids in shelf.items(): 
                if feed not in conf.names(): 
                    del_feeds.append(feed)
                    
                    try: 
<<<<<<< HEAD
                        Path(config.paths["static"]).joinpath('feed', '{}.html'.format(feed)).unlink()
                    except FileNotFoundError:
=======
                        os.remove(Path(static_path).joinpath('feed', '{}.html'.format(feed)))
                    except Exception:
>>>>>>> e5d1f817b9c100063a6da15ad48f7673757bf99a
                        logging.error('Failed to remove feed file for no longer defined feed: {}'.format(feed), exc_info=True)

                    for id_ in ids: 
                        try:
<<<<<<< HEAD
                            Path(config.paths["static"]).joinpath('alt', '{}.html'.format(id_)).unlink()
                        except FileNotFoundError: 
=======
                            os.remove(Path(static_path).joinpath('alt', '{}.html'.format(id_)))
                        except Exception: 
>>>>>>> e5d1f817b9c100063a6da15ad48f7673757bf99a
                            logging.error('Failed to remove feed alternate html files: {}, for no longer defined feed: {}'.format(id_, feed), exc_info=True)  

            try: # just as it is a bad idea to mutate dict during iteration on it, it is probably a bad idea for shelves.
                for feed in del_feeds:
                    del shelf[feed]                      
            except KeyError: 
                logging.error('Failed to remove alt id list for no longer defined feed from alternate_ids.shelf: {}'.format(feed), exc_info=True )

        # remove recieved mail uuids 
        with shelve.open(str(Path(config.paths["data"]).joinpath('mail_uuids.shelf'))) as shelf:
            del_feeds = []
            for feed in shelf.keys(): 
                if feed not in conf.names():
                    del_feeds.append(feed)
            try:
                for feed in del_feeds:
                    del shelf[feed]
            except KeyError: 
                logging.error('Failed to remove recieved mail uuid list for no longer defined feed from mail_uuids.shelf: {}'.format(feed), exc_info=True )

    @classmethod
    def generate_unique_alt_id(cls) -> str: 
        """ Generate a psuedo-random 30 character alphanumeric (lower case only) id that is not in alternates.shelf
        """
        with shelve.open(str(Path(config.paths["data"]).joinpath('alternates.shelf'))) as shelf:
            all_ids = []
            try: 
                for feed_ids in shelf.values(): 
                    if isinstance(feed_ids, list):
                        all_ids.extend(feed_ids)
            except (NameError, KeyError): # probably not necessary?
                pass

        random.seed(None, 2)
        alternate_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=30)) 
        while alternate_id in all_ids:
<<<<<<< HEAD
            alternate_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=30)) 
=======
            alternate_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=30)) 
>>>>>>> e5d1f817b9c100063a6da15ad48f7673757bf99a
        return alternate_id
