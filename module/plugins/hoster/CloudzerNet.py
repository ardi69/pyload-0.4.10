# -*- coding: utf-8 -*-

from pyload.plugin.internal.DeadHoster import DeadHoster


class CloudzerNet(DeadHoster):
    __name__    = "CloudzerNet"
    __type__    = "hoster"
    __version__ = "0.05"

    __pattern__ = r'https?://(?:www\.)?(cloudzer\.net/file/|clz\.to/(file/)?)\w+'
    __config__  = []

    __description__ = """Cloudzer.net hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("gs", "I-_-I-_-I@web.de"),
                       ("z00nx", "z00nx0@gmail.com"),
                       ("stickell", "l.stickell@yahoo.it")]
