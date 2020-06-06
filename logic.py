# -*- coding: utf-8 -*-
#########################################################
# python
import os
import sys
import traceback
import time
import re
import time

# third-party
import requests
from flask import Blueprint, request, Response, send_file, render_template, redirect, jsonify

# sjva 공용
from framework import db, scheduler
from framework.job import Job
from framework.util import Util

# 패키지
from .plugin import logger, package_name
from .model import ModelSetting

#########################################################
class Logic(object):
    db_default = { 
        'db_version' : '1',
        'tvh_username' : '',
        'tvh_password' : '',
        'tvh_url' : '',
        'tvh_auth' : '',
        'player_profile' : 'webtv-h264-aac-matroska',
        'tvh_proxy' : 'False',
        'proxy_profile' : 'True', #안씀
        'proxy_auto_start' : 'False',
        'plex_profile' : 'pass'
    }

    @staticmethod
    def db_init():
        try:
            for key, value in Logic.db_default.items():
                if db.session.query(ModelSetting).filter_by(key=key).count() == 0:
                    db.session.add(ModelSetting(key, value))
            db.session.commit()
            Logic.migration()
        except Exception as e: 
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())

    @staticmethod
    def plugin_load():
        try:
            Logic.db_init()
            from plugin import plugin_info
            Util.save_from_dict_to_json(plugin_info, os.path.join(os.path.dirname(__file__), 'info.json'))   
        except Exception as e: 
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())

    @staticmethod
    def plugin_unload():
        pass

    @staticmethod
    def migration():
        pass