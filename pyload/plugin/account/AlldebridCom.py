# -*- coding: utf-8 -*-

import re
import time
import xml.dom.minidom as dom

import BeautifulSoup

from pyload.plugin.Account import Account


class AlldebridCom(Account):
    __name    = "AlldebridCom"
    __type    = "account"
    __version = "0.23"

    __description = """AllDebrid.com account plugin"""
    __license     = "GPLv3"
    __authors     = [("Andy Voigt", "spamsales@online.de")]


    def loadAccountInfo(self, user, req):
        data = self.getAccountData(user)
        html = req.load("http://www.alldebrid.com/account/")
        soup = BeautifulSoup.BeautifulSoup(html)

        # Try to parse expiration date directly from the control panel page (better accuracy)
        try:
            time_text = soup.find('div', attrs={'class': 'remaining_time_text'}).strong.string

            self.logDebug("Account expires in: %s" % time_text)

            p = re.compile('\d+')
            exp_data = p.findall(time_text)
            exp_time = time.time() + int(exp_data[0]) * 24 * 60 * 60 + int(
                exp_data[1]) * 60 * 60 + (int(exp_data[2]) - 1) * 60

        # Get expiration date from API
        except Exception:
            data = self.getAccountData(user)
            html = req.load("http://www.alldebrid.com/api.php",
                            get={'action': "info_user", 'login': user, 'pw': data['password']})

            self.logDebug(html)

            xml = dom.parseString(html)
            exp_time = time.time() + int(xml.getElementsByTagName("date")[0].childNodes[0].nodeValue) * 24 * 60 * 60

        account_info = {"validuntil": exp_time, "trafficleft": -1}
        return account_info


    def login(self, user, data, req):
        html = req.load("http://www.alldebrid.com/register/",
                        get={'action'        : "login",
                             'login_login'   : user,
                             'login_password': data['password']},
                        decode=True)

        if "This login doesn't exist" in html \
           or "The password is not valid" in html \
           or "Invalid captcha" in html:
            self.wrongPassword()
