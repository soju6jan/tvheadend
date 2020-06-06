# -*- coding: utf-8 -*-
#########################################################
# python
import os
import sys
import traceback
import time
from datetime import datetime, timedelta
import logging
import urllib
import urllib2
import re
import time
from operator import itemgetter

# third-party
import requests
from requests.auth import HTTPDigestAuth, HTTPBasicAuth
from flask import Blueprint, request, Response, send_file, render_template, redirect, jsonify
from sqlalchemy import desc

# sjva 공용
from framework import db, scheduler
from framework.job import Job
from framework.util import Util


# 패키지
from .plugin import logger, package_name
from .model import ModelSetting

#########################################################

class LogicNormal(object):
    @staticmethod
    def get_response(api, tvh_username=None, tvh_password=None, tvh_url=None):
        if tvh_username is None:
            tvh_username = ModelSetting.get('tvh_username')
        if tvh_password is None:            
            tvh_password = ModelSetting.get('tvh_password')
        if tvh_url is None:
            tvh_url = ModelSetting.get('tvh_url')
        if tvh_url is None or tvh_url == '':
            return
        url = '%s%s' % (tvh_url, api)
        try:
            response = requests.get(url, auth=HTTPDigestAuth(tvh_username, tvh_password))
            if response.status_code == 200:
                return response
        except Exception as e: 
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())

        try:
            response = requests.get(url, auth=HTTPBasicAuth(tvh_username, tvh_password))
            if response.status_code == 200:
                return response
        except Exception as e: 
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())
        
        try:
            tmp = tvh_url.split('//')
            if len(tmp) == 2:
                url = '%s//%s:%s@%s%s' % (tmp[0], tvh_username, tvh_password, tmp[1], api)
                response = requests.get(url)
                if response.status_code == 200:
                    return response
        except Exception as e: 
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())
            

    @staticmethod
    def server_info(req):
        ret = {}
        try:
            tvh_username = req.form['tvh_username']
            tvh_password = req.form['tvh_password']
            tvh_url = req.form['tvh_url']
            response = LogicNormal.get_response('/api/serverinfo', tvh_username=tvh_username, tvh_password=tvh_password, tvh_url=tvh_url, )
            if response is not None:
                data = response.json()
                ret['ret'] = 'success'
                ret['data'] = data
            else:
                ret['ret'] = 'fail'
                ret['data'] = 'Url or Auth Fail!!!!'
        except Exception as e: 
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())
            ret['ret'] = 'error'
            ret['data'] = str(e)
        return ret
    
    @staticmethod
    def channel_list():
        try:
            tvh_auth = ModelSetting.get('tvh_auth')
            tvh_url = ModelSetting.get('tvh_url')

            response = LogicNormal.get_response('/api/channel/grid?start=0&limit=999999')
            if response is None:
                return
            channels = response.json()['entries']
            lineup = []
            for c in channels:
                if c['enabled']:
                    url = '%s/stream/channel/%s?auth=%s' % (tvh_url, c['uuid'], tvh_auth)
                    try:
                        number = float(c['number'])
                    except:
                        number = c['number']
                    lineup.append({'GuideNumber': number, 'GuideName': c['name'], 'URL': url, 'uuid':c['uuid']})
            
            response = LogicNormal.get_response('/api/epg/events/grid?start=0&limit=%s' % len(lineup))
            data = response.json()['entries']
            
            timestamp = int(time.time())
            for d in data:
                if d['start'] <= timestamp <= d['stop']:
                    for l in lineup:
                        if l['uuid'] == d['channelUuid']:
                            l['title'] = d['title']
                            break
            lineup = sorted(lineup, key=itemgetter('GuideNumber'))
            response = LogicNormal.get_response('/api/profile/list')
            data = response.json()['entries']
            ret = {}
            ret['lineup'] = lineup
            ret['profile'] = data
            ret['player_profile'] = ModelSetting.get('player_profile')
            return ret
        except Exception as e: 
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())
           
