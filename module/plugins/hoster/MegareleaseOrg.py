# -*- coding: utf-8 -*-

from pyload.plugin.internal.DeadHoster import DeadHoster


class MegareleaseOrg(DeadHoster):
    __name__    = "MegareleaseOrg"
    __type__    = "hoster"
    __version__ = "0.02"

    __pattern__ = r'https?://(?:www\.)?megarelease\.org/\w{12}'
    __config__  = []

    __description__ = """Megarelease.org hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("derek3x", "derek3x@vmail.me"),
                       ("stickell", "l.stickell@yahoo.it")]
