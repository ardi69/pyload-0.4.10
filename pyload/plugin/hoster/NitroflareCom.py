# -*- coding: utf-8 -*-

import re

from pyload.plugin.captcha.ReCaptcha import ReCaptcha
from pyload.plugin.internal.SimpleHoster import SimpleHoster


class NitroflareCom(SimpleHoster):
    __name    = "NitroflareCom"
    __type    = "hoster"
    __version = "0.12"

    __pattern = r'https?://(?:www\.)?nitroflare\.com/view/(?P<ID>[\w^_]+)'
    __config  = [("use_premium", "bool", "Use premium account if available", True)]

    __description = """Nitroflare.com hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("sahil", "sahilshekhawat01@gmail.com"),
                       ("Walter Purcaro", "vuolter@gmail.com"),
                       ("Stickell", "l.stickell@yahoo.it")]

    # URL_REPLACEMENTS = [("http://", "https://")]

    INFO_PATTERN    = r'title="(?P<N>.+?)".+>(?P<S>[\d.,]+) (?P<U>[\w^_]+)'
    OFFLINE_PATTERN = r'>File doesn\'t exist'

    LINK_FREE_PATTERN = r'(https?://[\w\-]+\.nitroflare\.com/.+?)"'

    RECAPTCHA_KEY        = "6Lenx_USAAAAAF5L1pmTWvWcH73dipAEzNnmNLgy"
    PREMIUM_ONLY_PATTERN = r'This file is available with Premium only'
    WAIT_PATTERN         = r'You have to wait (\d+ minutes)'
    # ERROR_PATTERN        = r'downloading is not possible'


    def handle_free(self, pyfile):
        # used here to load the cookies which will be required later
        self.load(pyfile.url, post={'goToFreePage': ""})

        self.load("http://nitroflare.com/ajax/setCookie.php", post={'fileId': self.info['pattern']['ID']})
        self.html = self.load("http://nitroflare.com/ajax/freeDownload.php",
                              post={'method': "startTimer", 'fileId': self.info['pattern']['ID']})

        self.checkErrors()

        try:
            js_file   = self.load("http://nitroflare.com/js/downloadFree.js?v=1.0.1")
            var_time  = re.search("var time = (\\d+);", js_file)
            wait_time = int(var_time.groups()[0])

        except Exception:
            wait_time = 60

        self.wait(wait_time)

        recaptcha = ReCaptcha(self)
        response, challenge = recaptcha.challenge(self.RECAPTCHA_KEY)

        self.html = self.load("http://nitroflare.com/ajax/freeDownload.php",
                              post={'method'                   : "fetchDownload",
                                    'recaptcha_challenge_field': challenge,
                                    'recaptcha_response_field' : response})

        if "The captcha wasn't entered correctly" in self.html:
            self.logWarning("The captcha wasn't entered correctly")
            return

        if "You have to fill the captcha" in self.html:
            self.logWarning("Captcha unfilled")
            return

        return super(NitroflareCom, self).handleFree(pyfile)
