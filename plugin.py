# -*- coding: utf-8 -*-
#########################################################
# python
import os
import sys
import traceback
import threading
import time
from io import StringIO

# third-party
import requests
from flask import Blueprint, request, Response, render_template, redirect, jsonify, redirect, send_file
from flask_login import login_user, logout_user, current_user, login_required

# sjva 공용
from framework.logger import get_logger
from framework import app, db, scheduler, check_api
from framework.util import Util
from system.model import ModelSetting as SystemModelSetting

            
# 패키지
package_name = __name__.split('.')[0]
logger = get_logger(package_name)

from .model import ModelSetting
from .logic import Logic
from .logic_normal import LogicNormal

#########################################################

blueprint = Blueprint(package_name, package_name, url_prefix='/%s' %  package_name, template_folder=os.path.join(os.path.dirname(__file__), 'templates'))

menu = {
    'main' : [package_name, 'Tvheadend'],
    'sub' : [
        ['setting', u'설정'], ['list', u'Player'], ['log', u'로그']
    ],
    'category' : 'tv'
}

plugin_info = {
    'version' : '1.0',
    'name' : 'tvheadend',
    'category_name' : 'tv',
    'developer' : 'soju6jan',
    'description' : u'TVHeadend 연결 플러그인',
    'home' : 'https://github.com/soju6jan/tvheadend',
    'more' : '',
}

def plugin_load():
    Logic.plugin_load()

def plugin_unload():
    Logic.plugin_unload()


#########################################################
# WEB Menu   
#########################################################
@blueprint.route('/')
def home():
    return redirect('/%s/setting' % package_name)

@blueprint.route('/%s/proxy' % package_name)
def r1():
    return redirect('/%s/proxy/discover.json' % package_name)


@blueprint.route('/<sub>')
@login_required
def first_menu(sub): 
    try:
        if sub == 'setting':
            from system.model import ModelSetting as SystemModelSetting
            arg = ModelSetting.to_dict()
            arg['ddns'] = SystemModelSetting.get('ddns')
            arg['url_epg'] = '%s/epg/api/%s' % (arg['ddns'], package_name)
            arg['url_m3u'] = '%s/%s/api/m3u?profile=pass' % (arg['ddns'], package_name)
            apikey = SystemModelSetting.get('auth_apikey')
            if SystemModelSetting.get_bool('auth_use_apikey'):
                arg['url_epg'] += '?apikey=%s' % apikey
                arg['url_m3u'] += '&apikey=%s' % apikey
            return render_template('%s_%s.html' % (package_name, sub), arg=arg)
        elif sub == 'list':
            arg = ModelSetting.to_dict()
            return render_template('%s_%s.html' % (package_name, sub), arg=arg)
        elif sub == 'proxy':
            return redirect('/%s/proxy/discover.json' % package_name)
        elif sub == 'log':
            return render_template('log.html', package=package_name)
        return render_template('sample.html', title='%s - %s' % (package_name, sub))
    except Exception as e: 
        logger.error('Exception:%s', e)
        logger.error(traceback.format_exc())

#########################################################
# For UI                                                          
#########################################################
@blueprint.route('/ajax/<sub>', methods=['GET', 'POST'])
@login_required
def ajax(sub):
    logger.debug('AJAX %s %s', package_name, sub)
    try:
        if sub == 'setting_save':
            ret = ModelSetting.setting_save(request)
            return jsonify(ret)
        elif sub == 'server_info':
            ret = LogicNormal.server_info(request)
            return jsonify(ret)
        elif sub == 'channel_list':
            ret = LogicNormal.channel_list()
            return jsonify(ret)
    except Exception as e: 
        logger.error('Exception:%s', e)
        logger.error(traceback.format_exc())
        

#########################################################
# API
#########################################################
@blueprint.route('/api/<sub>', methods=['GET', 'POST'])
@check_api
def api(sub):
    logger.debug('api %s %s', package_name, sub)
    try:
        if sub == 'm3u':
            profile = request.args.get('profile')
            format = request.args.get('format')
            response = LogicNormal.get_response('/playlist/channels.m3u?profile=%s' % profile)
            auth = ModelSetting.get('tvh_auth')
            data = response.text
            data = data.replace('profile=%s' % profile, 'profile=%s&auth=%s' % (profile, auth))
            if format == 'file':
                output_stream = StringIO(data) 
                response = Response(
                    output_stream.getvalue(), 
                    content_type='application/octet-stream',
                )
                response.headers["Content-Disposition"] = "attachment; filename=channels.m3u"
                return response 
            else:
                return data
    except Exception as e: 
        logger.error('Exception:%s', e)
        logger.error(traceback.format_exc())


#########################################################
# Proxy
#########################################################
@blueprint.route('/proxy/<sub>', methods=['GET', 'POST'])
def proxy(sub):
    logger.debug('proxy %s %s', package_name, sub)
    try:
        if sub == 'discover.json':
            ddns = SystemModelSetting.get('ddns')
            data = {"FriendlyName":"HDHomeRun CONNECT","ModelNumber":"HDHR4-2US","FirmwareName":"hdhomerun4_atsc","FirmwareVersion":"20190621","DeviceID":"104E8010","DeviceAuth":"UF4CFfWQh05c3jROcArmAZaf","BaseURL":"%s/tvheadend/proxy" % ddns,"LineupURL":"%s/tvheadend/proxy/lineup.json" % ddns,"TunerCount":2}
            return jsonify(data)
        elif sub == 'lineup_status.json':
            data = {"ScanInProgress":0,"ScanPossible":1,"Source":"Cable","SourceList":["Antenna","Cable"]}
            return jsonify(data)
        elif sub == 'lineup.json':
            tvh_url = ModelSetting.get('tvh_url')
            tvh_auth = ModelSetting.get('tvh_auth')
            profile = ModelSetting.get('plex_profile')
            r = LogicNormal.get_response('/api/channel/grid?start=0&limit=99999')
            channels = r.json()['entries']
            lineup = []
            for c in channels:
                if c['enabled']:
                    url = '%s/stream/channel/%s?auth=%s&profile=%s' % (tvh_url, c['uuid'], tvh_auth, profile)
                    lineup.append({'GuideNumber': str(c['number']), 'GuideName': c['name'], 'URL': url})
            return jsonify(lineup)
    except Exception as e: 
        logger.error('Exception:%s', e)
        logger.error(traceback.format_exc())
                
