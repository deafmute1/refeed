# Author: 'Ethan Djeric <me@ethandjeric.com>'

# stdlib
import logging
from datetime import datetime
import time 
from pathlib import Path
import signal
# pypi
import schedule
# refeed
from . import feed, mail, config, global_config

class Run():
    """  
    """
    def __init__(self): 
        signal.signal(signal.SIGHUP, self._exit)
        signal.signal(signal.SIGTERM, self._exit)
        self.run = schedule.Scheduler()
        self._schedule()
        self._main()

    def _schedule(self):
        conf = config.App(global_config.config_path)
        # add schedules
        self.run.every(conf.wait_to_update()).minutes.do(_Tasks.generate_feeds_from_new_mail)
        self.run.every(1).week.do(_Tasks.cleanup_feeds)

    def _main(self): 
        _Tasks.cleanup_feeds() # run once, as job will not run unless this has been running for 1 week
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
        conf = config.Feed(global_config.config_path)
        for feed_name in conf.names():
            logging.info('feed_name_tasks: {}'.format(feed_name))
            with feed.Feed(feed_name) as f:
                try:
                    # IMAP doesnt specify TZ for 'INTERNALDATE', so 2 days is the samllest value I'm happy with.
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



