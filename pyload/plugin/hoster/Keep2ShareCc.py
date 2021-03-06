# -*- coding: utf-8 -*-

import re
import urlparse

from pyload.plugin.captcha.ReCaptcha import ReCaptcha
from pyload.plugin.internal.SimpleHoster import SimpleHoster


class Keep2ShareCc(SimpleHoster):
    __name    = "Keep2ShareCc"
    __type    = "hoster"
    __version = "0.21"

    __pattern = r'https?://(?:www\.)?(keep2share|k2s|keep2s)\.cc/file/(?P<ID>\w+)'
    __config  = [("use_premium", "bool", "Use premium account if available", True)]

    __description = """Keep2Share.cc hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("stickell", "l.stickell@yahoo.it"),
                       ("Walter Purcaro", "vuolter@gmail.com")]


    URL_REPLACEMENTS = [(__pattern + ".*", "http://keep2s.cc/file/\g<ID>")]

    NAME_PATTERN = r'File: <span>(?P<N>.+)</span>'
    SIZE_PATTERN = r'Size: (?P<S>[^<]+)</div>'

    OFFLINE_PATTERN      = r'File not found or deleted|Sorry, this file is blocked or deleted|Error 404'
    TEMP_OFFLINE_PATTERN = r'Downloading blocked due to'

    LINK_FREE_PATTERN    = r'"(.+?url.html\?file=.+?)"|window\.location\.href = \'(.+?)\';'
    LINK_PREMIUM_PATTERN = r'window\.location\.href = \'(.+?)\';'

    CAPTCHA_PATTERN = r'src="(/file/captcha\.html.+?)"'

    WAIT_PATTERN         = r'Please wait ([\d:]+) to download this file'
    TEMP_ERROR_PATTERN   = r'>\s*(Download count files exceed|Traffic limit exceed|Free account does not allow to download more than one file at the same time)'
    ERROR_PATTERN        = r'>\s*(Free user can\'t download large files|You no can access to this file|This download available only for premium users|This is private file)'


    def checkErrors(self):
        m = re.search(self.TEMP_ERROR_PATTERN, self.html)
        if m:
            self.info['error'] = m.group(1)
            self.wantReconnect = True
            self.retry(wait_time=30 * 60, reason=m.group(0))

        m = re.search(self.ERROR_PATTERN, self.html)
        if m:
            errmsg = self.info['error'] = m.group(1)
            self.error(errmsg)

        m = re.search(self.WAIT_PATTERN, self.html)
        if m:
            self.logDebug("Hoster told us to wait for %s" % m.group(1))

            # string to time convert courtesy of https://stackoverflow.com/questions/10663720
            ftr = [3600, 60, 1]
            wait_time = sum(a * b for a, b in zip(ftr, map(int, m.group(1).split(':'))))

            self.wantReconnect = True
            self.retry(wait_time=wait_time, reason="Please wait to download this file")

        self.info.pop('error', None)


    def handle_free(self, pyfile):
        self.fid  = re.search(r'<input type="hidden" name="slow_id" value="(.+?)">', self.html).group(1)
        self.html = self.load(pyfile.url, post={'yt0': '', 'slow_id': self.fid})

        # self.logDebug(self.fid)
        # self.logDebug(pyfile.url)

        self.checkErrors()

        m = re.search(self.LINK_FREE_PATTERN, self.html)
        if m is None:
            self.handleCaptcha()
            self.wait(31)
            self.html = self.load(pyfile.url)

            m = re.search(self.LINK_FREE_PATTERN, self.html)
            if m is None:
                self.error(_("Free download link not found"))

        self.link = m.group(1)


    def handleCaptcha(self):
        post_data = {'free'               : 1,
                     'freeDownloadRequest': 1,
                     'uniqueId'           : self.fid,
                     'yt0'                : ''}

        m = re.search(r'id="(captcha\-form)"', self.html)
        self.logDebug("captcha-form found %s" % m)

        m = re.search(self.CAPTCHA_PATTERN, self.html)
        self.logDebug("CAPTCHA_PATTERN found %s" % m)
        if m:
            captcha_url = urlparse.urljoin("http://keep2s.cc/", m.group(1))
            post_data['CaptchaForm[code]'] = self.decryptCaptcha(captcha_url)
        else:
            recaptcha = ReCaptcha(self)
            response, challenge = recaptcha.challenge()
            post_data.update({'recaptcha_challenge_field': challenge,
                              'recaptcha_response_field' : response})

        self.html = self.load(self.pyfile.url, post=post_data)

        if 'verification code is incorrect' not in self.html:
            self.correctCaptcha()
        else:
            self.invalidCaptcha()
