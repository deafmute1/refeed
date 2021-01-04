# Author: 'Ethan Djeric <me@ethandjeric.com>'

# stdlib
import logging
from datetime import datetime
import time 
from pathlib import Path
# pypi
import schedule
# refeed
from . import feed, mail, config, gconfig

log_path = gconfig.log_path
config_path = gconfig.config_path

class Run():
    """  
    """
    def __init__(self): 
        self.startup()
        self.main()

    def startup(self):
        conf = config.App(config_path)
        loglevel = conf.log_level()
        # log to file
        logging.basicConfig(filename=log_path, level=getattr(logging, loglevel), filemode='a')
        # log to console 
        console = logging.StreamHandler()
        logging.getLogger('').addHandler(console) # '' = root logger
        # startup tasks
        _Tasks.cleanup_feeds()
        # add schedules
        schedule.every(conf.wait_to_update()).minutes.do(_Tasks.generate_feeds_from_new_mail())
        schedule.every(1).week.do(_Tasks.cleanup_feeds())

    def main(self): 
        while True: 
            schedule.run_pending()
            time.sleep(1)

class _Tasks():
    @classmethod
    def generate_feeds_from_new_mail(cls):
        logging.info('Mail fetch and feed generation job starting')
        conf = config.Feed(config_path)
        for feed_name in conf.names():
            logging.debug('feed_name_tasks: {}',format(feed_name))
            with feed.Feed(feed_name) as f:
                # IMAP doesnt specify TZ for 'INTERNALDATE', so 2 days is the samllest value I'm happy with.
                success = f.add_entries_from_dict_if_new(mail.MailFetch.new_mail(feed_name, 2))
                if not success: 
                        logging.error('Some error further up the log has caused failure to be reported and job to be canceled before generate_feed()')
                        return schedule.CancelJob
                f.generate_feed()
            logging.info('Feed Generated')

    @classmethod
    def cleanup_feeds(cls):
        logging.info('Cleaning up unwanted feeds')
        return feed.FeedTools.cleanup_feeds()



