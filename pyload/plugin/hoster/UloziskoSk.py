# -*- coding: utf-8 -*-

import re
import urlparse

from pyload.plugin.internal.SimpleHoster import SimpleHoster


class UloziskoSk(SimpleHoster):
    __name    = "UloziskoSk"
    __type    = "hoster"
    __version = "0.25"

    __pattern = r'http://(?:www\.)?ulozisko\.sk/.+'
    __config  = [("use_premium", "bool", "Use premium account if available", True)]

    __description = """Ulozisko.sk hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("zoidberg", "zoidberg@mujmail.cz")]


    NAME_PATTERN = r'<div class="down1">(?P<N>[^<]+)</div>'
    SIZE_PATTERN = ur'Veľkosť súboru: <strong>(?P<S>[\d.,]+) (?P<U>[\w^_]+)</strong><br />'
    OFFLINE_PATTERN = ur'<span class = "red">Zadaný súbor neexistuje z jedného z nasledujúcich dôvodov:</span>'

    LINK_FREE_PATTERN = r'<form name = "formular" action = "(.+?)" method = "post">'
    ID_PATTERN = r'<input type = "hidden" name = "id" value = "(.+?)" />'
    CAPTCHA_PATTERN = r'<img src="(/obrazky/obrazky\.php\?fid=.+?)" alt="" />'
    IMG_PATTERN = ur'<strong>PRE ZVÄČŠENIE KLIKNITE NA OBRÁZOK</strong><br /><a href = "(.+?)">'


    def process(self, pyfile):
        self.html = self.load(pyfile.url, decode=True)
        self.getFileInfo()

        m = re.search(self.IMG_PATTERN, self.html)
        if m:
            self.link = "http://ulozisko.sk" + m.group(1)
        else:
            self.handle_free(pyfile)


    def handle_free(self, pyfile):
        m = re.search(self.LINK_FREE_PATTERN, self.html)
        if m is None:
            self.error(_("LINK_FREE_PATTERN not found"))
        parsed_url = 'http://www.ulozisko.sk' + m.group(1)

        m = re.search(self.ID_PATTERN, self.html)
        if m is None:
            self.error(_("ID_PATTERN not found"))
        id = m.group(1)

        self.logDebug("URL:" + parsed_url + ' ID:' + id)

        m = re.search(self.CAPTCHA_PATTERN, self.html)
        if m is None:
            self.error(_("CAPTCHA_PATTERN not found"))

        captcha_url = urlparse.urljoin("http://www.ulozisko.sk", m.group(1))
        captcha = self.decryptCaptcha(captcha_url, cookies=True)

        self.logDebug("CAPTCHA_URL:" + captcha_url + ' CAPTCHA:' + captcha)

        self.download(parsed_url,
                      post={"antispam": captcha,
                            "id"      : id,
                            "name"    : pyfile.name,
                            "but"     : "++++STIAHNI+S%DABOR++++"})
