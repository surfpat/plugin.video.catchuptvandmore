# -*- coding: utf-8 -*-
'''
    Catch-up TV & More
    Copyright (C) 2017  SylvainCecchetto

    This file is part of Catch-up TV & More.

    Catch-up TV & More is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

    Catch-up TV & More is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License along
    with Catch-up TV & More; if not, write to the Free Software Foundation,
    Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
'''

import json
import xbmcgui
from resources.lib import utils
from resources.lib import common
import ast


# TODO
# Add Live TV
# Add RMCDECOUVERTE / Find API RMCDECOUVERTE ? BS ?
# Add Download Video

url_token = 'http://api.nextradiotv.com/%s-applications/'
#channel

url_menu = 'http://www.bfmtv.com/static/static-mobile/bfmtv/' \
           'ios-smartphone/v0/configuration.json'

url_replay = 'http://api.nextradiotv.com/%s-applications/%s/' \
             'getPage?pagename=replay'
# channel, token

url_show = 'http://api.nextradiotv.com/%s-applications/%s/' \
           'getVideosList?category=%s&count=100&page=%s'
# channel, token, category, page_number

url_video = 'http://api.nextradiotv.com/%s-applications/%s/' \
            'getVideo?idVideo=%s'
# channel, token, video_id


@common.plugin.cached(common.cache_time)
def get_token(channel_name):
    file_token = utils.get_webcontent(url_token % (channel_name))
    token_json = json.loads(file_token)
    return token_json['session']['token'].encode('utf-8')


def channel_entry(params):
    if 'list_shows' in params.next:
        return list_shows(params)
    elif 'list_videos' in params.next:
        return list_videos(params)
    elif 'play' in params.next:
        return get_video_url(params)


@common.plugin.cached(common.cache_time)
def list_shows(params):
    # Create categories list
    shows = []

    if params.next == 'list_shows_1':
        file_path = utils.download_catalog(
            url_replay % (params.channel_name, get_token(params.channel_name)),
            '%s.json' % (params.channel_name))
        file_categories = open(file_path).read()
        json_categories = json.loads(file_categories)
        json_categories = json_categories['page']['contents'][0]
        json_categories = json_categories['elements'][0]['items']

        for categories in json_categories:
            title = categories['title'].encode('utf-8')
            image_url = categories['image_url'].encode('utf-8')
            category = categories['categories'].encode('utf-8')

            shows.append({
                'label': title,
                'thumb': image_url,
                'url': common.plugin.get_url(
                    action='channel_entry',
                    category=category,
                    next='list_videos_1',
                    title=title,
                    page='1',
                    window_title=title
                )
            })

        return common.plugin.create_listing(
            shows,
            sort_methods=(
                common.sp.xbmcplugin.SORT_METHOD_UNSORTED,
                common.sp.xbmcplugin.SORT_METHOD_LABEL
            )
        )


#@common.plugin.cached(common.cache_time)
def list_videos(params):
    videos = []
    if 'previous_listing' in params:
        videos = ast.literal_eval(params['previous_listing'])

    if params.next == 'list_videos_1':
        file_path = utils.download_catalog(
            url_show % (
                params.channel_name, 
		get_token(params.channel_name),
                params.category,
                params.page),
            '%s_%s_%s.json' % (
                params.channel_name,
                params.category,
                params.page))
        file_show = open(file_path).read()
        json_show = json.loads(file_show)

        for video in json_show['videos']:
            video_id = video['video'].encode('utf-8')
            video_id_ext = video['id_ext'].encode('utf-8')
            category = video['category'].encode('utf-8')
            title = video['title'].encode('utf-8')
            description = video['description'].encode('utf-8')
            begin_date = video['begin_date'] # 1486725600,
            image = video['image'].encode('utf-8')
            duration = video['video_duration_ms'] / 1000

            info = {
                'video': {
                    'title': title,
                    'plot': description,
                    #'aired': aired,
                    #'date': date,
                    'duration': duration,
                    #'year': year,
                    'genre': category,
                    'mediatype': 'tvshow'
                }
            }
            	
            videos.append({
                'label': title,
                'thumb': image,
                'url': common.plugin.get_url(
                    action='channel_entry',
                    next='play',
                    video_id=video_id,
                    video_id_ext=video_id_ext
                ),
                'is_playable': True,
                'info': info
            })

        # More videos...
        videos.append({
            'label': common.addon.get_localized_string(30100),
            'url': common.plugin.get_url(
                action='channel_entry',
                category=params.category,
                next='list_videos_1',
                title=title,
                page=str(int(params.page) + 1),
                window_title=params.window_title,
                update_listing=True,
                previous_listing=str(videos)
            )

        })

        return common.plugin.create_listing(
            videos,
            sort_methods=(
                common.sp.xbmcplugin.SORT_METHOD_UNSORTED,
                common.sp.xbmcplugin.SORT_METHOD_DURATION,
                common.sp.xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE,
                common.sp.xbmcplugin.SORT_METHOD_GENRE,
                common.sp.xbmcplugin.SORT_METHOD_UNSORTED
            ),
            content='tvshows',
            update_listing='update_listing' in params,
        )


#@common.plugin.cached(common.cache_time)
def get_video_url(params):
    file_medias = utils.get_webcontent(
        url_video % (params.channel_name, get_token(params.channel_name), params.video_id))
    json_parser = json.loads(file_medias)

    video_streams = json_parser['video']['medias']
	
    desired_quality = common.plugin.get_setting('quality')
	
    if desired_quality == "DIALOG":
	all_datas_videos = []
	for datas in video_streams:
	    new_list_item = xbmcgui.ListItem()
	    new_list_item.setLabel("Video Height : " + str(datas['frame_height']) + " (Encoding : " + str(datas['encoding_rate']) + ")")
	    new_list_item.setPath(datas['video_url'])
	    all_datas_videos.append(new_list_item)
		
	seleted_item = xbmcgui.Dialog().select("Choose Stream", all_datas_videos)
		
	return all_datas_videos[seleted_item].getPath().encode('utf-8')

    elif desired_quality == 'BEST':
	#GET LAST NODE (VIDEO BEST QUALITY)
	url_best_quality = ''
	for datas in video_streams:
	    url_best_quality = datas['video_url'].encode('utf-8')
	return url_best_quality
    else:
	#DEFAULT VIDEO
        return json_parser['video']['video_url'].encode('utf-8')
