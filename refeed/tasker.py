# Author: 'Ethan Djeric <me@ethandjeric.com>'

# STDLIB
import logging
from datetime import datetime
import time 
from pathlib import Path
import signal

# 3RD PARTY 
import schedule

# INTERNAL 
""" If we use the form `import x`, we can modify x.var. 
 However, with the form `from . import x`(relative or absolute), we cannot.
 The second form, where the namespace is modified, is equivalent to setting 
 the value of the import attrs to a module-specific global"""
import feed, mail, config

class Run():
    """ The main logic and scheduling for refeed.
        Run from refeed.main().
    """
    def __init__(self): 
        signal.signal(signal.SIGHUP, self._exit)
        signal.signal(signal.SIGTERM, self._exit)
        self.run = schedule.Scheduler()
        conf = config.App(config.paths["config"])

        # add tasks to scheduler
        self.run.every(conf.wait_to_update()).minutes.do(_Tasks.generate_feeds_from_new_mail)
        self.run.every(1).week.do(_Tasks.cleanup_feeds)

        # Main 
        # Startup tasks 
        _Tasks.cleanup_feeds() 
        _Tasks.make_run_dirs() 

        # Recurring tasks 
        while self.run.jobs != []: 
            self.run.run_pending()
            time.sleep(1)

    def _exit(self):
        logging.critical('SIGHUP or SIGTERM sent to refeed, exiting after finishing currently in progress jobs.')
        self.run.clear()

class _Tasks():
    @classmethod
    def generate_feeds_from_new_mail(cls):
        logging.info('Mail fetch and feed generation job starting')
        conf = config.Feed(config.paths["config"])
        for feed_name in conf.names():
            logging.info('feed_name_tasks: {}'.format(feed_name))
            with feed.Feed(feed_name) as f:
                try:
                    # IMAP doesnt specify TZ for 'INTERNALDATE', so 2 days is the smallest value I'm happy with.
                    new_mail = mail.MailFetch.new_mail(feed_name, 2)
                    if mail is None: 
                        logging.warning('mail.MailFetch.new_mail returned None. Either there have been no emails recieved at server matching filter for 2 days or an unhandled error occured. Ending feed generation job for {}'.format(feed_name) )
                        return schedule.CancelJob
                except (mail.ConfigError, mail.GenericHandledException):
                    logging.exception('Handled exception raised in mail.MailFetch.new_mail({f}). Ending feed generation job for {f}'.format(f=feed_name))
                    return schedule.CancelJob

                try: 
                    f.add_entries_from_dict_if_new(new_mail)
                except Exception:
                    logging.exception('Unknown error occured in feed.Feed.add_entries_from_dict_if_new(). Skipping feed generation for {}'.format(feed_name))
                    return schedule.CancelJob

                try: 
                    f.generate_feed()
                except Exception:
                    logging.exception('Unknown error occured in feed.Feed.generate_feed(). Skipping feed generation for {}'.format(feed_name))
                    return schedule.CancelJob
                    
            logging.info('Feed Generated')
            return 0

    @classmethod
    def cleanup_feeds(cls):
        logging.info('Cleaning up unwanted feeds')
        feed.FeedTools.cleanup_feeds()

    @classmethod 
    def make_run_dirs(cls):
        for name, path in config.paths.values():
            if config.paths_flag_dir[name]:
                try: 
                    path.mkdir(parents=True)
                except FileExistsError:
                    logging.info("Directory {} from config.paths[{}] not created as it already exists.".format(str(path), name))
                else:
                    logging.info("Directory {} created".format(str(path)))
