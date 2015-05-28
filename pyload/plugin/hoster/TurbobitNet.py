# -*- coding: utf-8 -*-

import binascii
import pycurl
import random
import re
import time
import urllib

import Crypto

from pyload.network.RequestFactory import getURL
from pyload.plugin.captcha.ReCaptcha import ReCaptcha
from pyload.plugin.internal.SimpleHoster import SimpleHoster, timestamp


class TurbobitNet(SimpleHoster):
    __name    = "TurbobitNet"
    __type    = "hoster"
    __version = "0.19"

    __pattern = r'http://(?:www\.)?turbobit\.net/(?:download/free/)?(?P<ID>\w+)'
    __config  = [("use_premium", "bool", "Use premium account if available", True)]

    __description = """Turbobit.net hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("zoidberg", "zoidberg@mujmail.cz"),
                       ("prOq", "")]


    URL_REPLACEMENTS = [(__pattern + ".*", "http://turbobit.net/\g<ID>.html")]

    COOKIES = [("turbobit.net", "user_lang", "en")]

    NAME_PATTERN = r'id="file-title">(?P<N>.+?)<'
    SIZE_PATTERN = r'class="file-size">(?P<S>[\d.,]+) (?P<U>[\w^_]+)'
    OFFLINE_PATTERN = r'<h2>File Not Found</h2>|html\(\'File (?:was )?not found'

    LINK_FREE_PATTERN = LINK_PREMIUM_PATTERN = r'(/download/redirect/[^"\']+)'

    LIMIT_WAIT_PATTERN = r'<div id=\'timeout\'>(\d+)<'
    CAPTCHA_PATTERN    = r'<img alt="Captcha" src="(.+?)"'


    def handle_free(self, pyfile):
        self.html = self.load("http://turbobit.net/download/free/%s" % self.info['pattern']['ID'],
                              decode=True)

        rtUpdate = self.getRtUpdate()

        self.solveCaptcha()

        self.req.http.c.setopt(pycurl.HTTPHEADER, ["X-Requested-With: XMLHttpRequest"])

        self.html = self.load(self.getDownloadUrl(rtUpdate))

        self.req.http.c.setopt(pycurl.HTTPHEADER, ["X-Requested-With:"])

        m = re.search(self.LINK_FREE_PATTERN, self.html)
        if m:
            self.link = m.group(1)


    def solveCaptcha(self):
        for _i in xrange(5):
            m = re.search(self.LIMIT_WAIT_PATTERN, self.html)
            if m:
                wait_time = int(m.group(1))
                self.wait(wait_time, wait_time > 60)
                self.retry()

            action, inputs = self.parseHtmlForm("action='#'")
            if not inputs:
                self.error(_("Captcha form not found"))
            self.logDebug(inputs)

            if inputs['captcha_type'] == 'recaptcha':
                recaptcha = ReCaptcha(self)
                inputs['recaptcha_response_field'], inputs['recaptcha_challenge_field'] = recaptcha.challenge()
            else:
                m = re.search(self.CAPTCHA_PATTERN, self.html)
                if m is None:
                    self.error(_("captcha"))
                captcha_url = m.group(1)
                inputs['captcha_response'] = self.decryptCaptcha(captcha_url)

            self.logDebug(inputs)
            self.html = self.load(self.url, post=inputs)

            if '<div class="captcha-error">Incorrect, try again!<' in self.html:
                self.invalidCaptcha()
            else:
                self.correctCaptcha()
                break
        else:
            self.fail(_("Invalid captcha"))


    def getRtUpdate(self):
        rtUpdate = self.retrieve("rtUpdate")
        if not rtUpdate:
            if self.retrieve("version") != self.__version \
               or int(self.retrieve("timestamp", 0)) + 86400000 < timestamp():
                # that's right, we are even using jdownloader updates
                rtUpdate = getURL("http://update0.jdownloader.org/pluginstuff/tbupdate.js")
                rtUpdate = self.decrypt(rtUpdate.splitlines()[1])
                # but we still need to fix the syntax to work with other engines than rhino
                rtUpdate = re.sub(r'for each\(var (\w+) in(\[[^\]]+\])\)\{',
                                  r'zza=\2;for(var zzi=0;zzi<zza.length;zzi++){\1=zza[zzi];', rtUpdate)
                rtUpdate = re.sub(r"for\((\w+)=", r"for(var \1=", rtUpdate)

                self.store("rtUpdate", rtUpdate)
                self.store("timestamp", timestamp())
                self.store("version", self.__version)
            else:
                self.logError(_("Unable to download, wait for update..."))
                self.tempOffline()

        return rtUpdate


    def getDownloadUrl(self, rtUpdate):
        self.req.http.lastURL = self.url

        m = re.search("(/\w+/timeout\.js\?\w+=)([^\"\'<>]+)", self.html)
        if m:
            url = "http://turbobit.net%s%s" % m.groups()
        else:
            url = "http://turbobit.net/files/timeout.js?ver=%s" % "".join(random.choice('0123456789ABCDEF') for _i in xrange(32))

        fun = self.load(url)

        self.setWait(65, False)

        for b in [1, 3]:
            self.jscode = "var id = \'%s\';var b = %d;var inn = \'%s\';%sout" % (
                          self.info['pattern']['ID'], b, urllib.quote(fun), rtUpdate)

            try:
                out = self.js.eval(self.jscode)
                self.logDebug("URL", self.js.engine, out)
                if out.startswith('/download/'):
                    return "http://turbobit.net%s" % out.strip()

            except Exception, e:
                self.logError(e)
        else:
            if self.retries >= 2:
                # retry with updated js
                self.delStorage("rtUpdate")
            else:
                self.retry()

        self.wait()


    def decrypt(self, data):
        cipher = Crypto.Cipher.ARC4.new(binascii.hexlify('E\x15\xa1\x9e\xa3M\xa0\xc6\xa0\x84\xb6H\x83\xa8o\xa0'))
        return binascii.unhexlify(cipher.encrypt(binascii.unhexlify(data)))


    def getLocalTimeString(self):
        lt = time.localtime()
        tz = time.altzone if lt.tm_isdst else time.timezone
        return "%s GMT%+03d%02d" % (time.strftime("%a %b %d %Y %H:%M:%S", lt), -tz // 3600, tz % 3600)
