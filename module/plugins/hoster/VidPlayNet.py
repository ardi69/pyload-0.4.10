# -*- coding: utf-8 -*-
#
# Test links:
#   http://vidplay.net/38lkev0h3jv0

from pyload.plugin.internal.XFSHoster import XFSHoster


class VidPlayNet(XFSHoster):
    __name__    = "VidPlayNet"
    __type__    = "hoster"
    __version__ = "0.04"

    __pattern__ = r'https?://(?:www\.)?vidplay\.net/\w{12}'

    __description__ = """VidPlay.net hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("t4skforce", "t4skforce1337[AT]gmail[DOT]com")]


    NAME_PATTERN = r'<b>Password:</b></div>\s*<h[1-6]>(?P<N>[^<]+)</h[1-6]>'
