# -*- coding: utf-8 -*-

import re

from pyload.plugin.Hoster import Hoster
from pyload.utils import html_unescape


class RedtubeCom(Hoster):
    __name    = "RedtubeCom"
    __type    = "hoster"
    __version = "0.20"

    __pattern = r'http://(?:www\.)?redtube\.com/\d+'

    __description = """Redtube.com hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("jeix", "jeix@hasnomail.de")]


    def process(self, pyfile):
        self.download_html()
        if not self.file_exists():
            self.offline()

        pyfile.name = self.get_file_name()
        self.download(self.get_file_url())


    def download_html(self):
        url = self.pyfile.url
        self.html = self.load(url)


    def get_file_url(self):
        """Returns the absolute downloadable filepath"""

        if not self.html:
            self.download_html()

        file_url = html_unescape(re.search(r'hashlink=(http.*?)"', self.html).group(1))

        return file_url


    def get_file_name(self):
        if not self.html:
            self.download_html()

        return re.search('<title>(.*?)- RedTube - Free Porn Videos</title>', self.html).group(1).strip() + ".flv"


    def file_exists(self):
        if not self.html:
            self.download_html()

        if re.search(r'This video has been removed.', self.html):
            return False
        else:
            return True
