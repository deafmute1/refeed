#!/usr/bin/env python
# -*- coding: utf-8 -*-

import refeed
from pathlib import Path 
import yaml

test_config_path = Path(__file__).parent.joinpath('data', 'public', 'config.yaml').resolve() 

def test_conf_path():
    refeed.config.paths["config"] = test_config_path 
    assert refeed.config.paths["config"] == test_config_path 

def test_PullConfig():
    yaml_dict = {
                'app': {'log_level': 'WARNING', 'wait_to_update': 5, 'static_path': '/var/www/html/refeed', 'log_parh': '/var/log/refeed/root.log'}, 
                'accounts': {'unique-account-name': {'server': {'host': 'mail.example.com', 'port': 993, 'ssl': True, 'stream': False}, 
                    'auth': {'auth_type': 'login', 'user': 'user@example.com', 'password': 'password123'}}}, 
                'feeds': {'unique-feed-name': {'folder': 'INBOX', 'account_name': 'my_account_name', 'alternate_cache': 25, 
                    'filters': {'date': {'OR': 'python regex here'}, 'from_': {'AND': 'python regex here', 'EXCLUDE': 'python regex here'}}, 
                    'feed_info': {'protocol': 'https://', 'fqdn': 'example.com', 'author-name': 'John Doe', 'language': 'en', 'logo': 'logo.png'}}}
                }
    refeed.config.PullConfig()
    assert refeed.config.loaded_yaml == yaml_dict
