# -*- coding: utf-8 -*-
#
# Test links:
#   http://d-h.st/users/shine/?fld_id=37263#files

import re
import urlparse

from pyload.plugin.internal.SimpleCrypter import SimpleCrypter


class DevhostSt(SimpleCrypter):
    __name    = "DevhostSt"
    __type    = "crypter"
    __version = "0.05"

    __pattern = r'http://(?:www\.)?d-h\.st/users/(?P<USER>\w+)(/\?fld_id=(?P<ID>\d+))?'
    __config  = [("use_premium"       , "bool", "Use premium account if available"   , True),
                   ("use_subfolder"     , "bool", "Save package to subfolder"          , True),
                   ("subfolder_per_pack", "bool", "Create a subfolder for each package", True)]

    __description = """d-h.st folder decrypter plugin"""
    __license     = "GPLv3"
    __authors     = [("zapp-brannigan", "fuerst.reinje@web.de"),
                       ("Walter Purcaro", "vuolter@gmail.com")]


    LINK_PATTERN    = r'(?:/> |;">)<a href="(.+?)"(?!>Back to \w+<)'
    OFFLINE_PATTERN = r'"/cHP">test\.png<'


    def checkNameSize(self, getinfo=True):
        if not self.info or getinfo:
            self.logDebug("File info (BEFORE): %s" % self.info)
            self.info.update(self.getInfo(self.pyfile.url, self.html))
            self.logDebug("File info (AFTER): %s"  % self.info)

        try:
            if self.info['pattern']['ID'] == "0":
                raise

            p = r'href="(.+?)">Back to \w+<'
            m = re.search(p, self.html)
            html = self.load(urlparse.urljoin("http://d-h.st", m.group(1)),
                             cookies=False)

            p = '\?fld_id=%s.*?">(.+?)<' % self.info['pattern']['ID']
            m = re.search(p, html)
            self.pyfile.name = m.group(1)

        except Exception, e:
            self.logDebug(e)
            self.pyfile.name = self.info['pattern']['USER']

        try:
            folder = self.info['folder'] = self.pyfile.name

        except Exception:
            pass
        self.logDebug("File name: %s"   % self.pyfile.name,
                      "File folder: %s" % self.pyfile.name)
