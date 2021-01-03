__author__ = 'Ethan Djeric <me@ethandjeric.com>'

# stdlib
import logging
from datetime import datetime
import time 
# pypi
import schedule
# refeed
from . import feed, mail, config


class Run():
    """  
    """
    def __init__(self): 
        # startup tasks
        feed.FeedTools.cleanup_feeds()
        #scheduled tasks
        schedule.every(config.App.wait_to_update()).minutes.do(_Tasks.generate_feeds_from_new_mail())
        schedule.every(1).week.do(feed.FeedTools.cleanup_feeds())
        # main loop
        while True: 
            schedule.run_pending()
            time.sleep(1)

class _Tasks():
    @classmethod
    def generate_feeds_from_new_mail(cls):
        logging.info('Mail fetch and feed generation job starting')
        for feed_name in config.Feed().names():
            with feed.Feed() as feed:
                # IMAP doesnt specify TZ for 'INTERNALDATE', so 2 days is the samllest value I'm happy with.
                feed.add_entries_from_dict_if_new(mail.MailFetch.new_mail(2))
                feed.generate_feed()
                logging.info('Feed Generated')