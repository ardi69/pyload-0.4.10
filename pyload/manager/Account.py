# -*- coding: utf-8 -*-

from __future__ import with_statement

import os
import shutil
import threading

from pyload.manager.Event import AccountUpdateEvent
from pyload.utils import lock


ACC_VERSION = 1


class AccountManager(object):
    """Manages all accounts"""

    def __init__(self, core):
        """Constructor"""

        self.core = core
        self.lock = threading.Lock()

        self.initPlugins()
        self.saveAccounts()  #: save to add categories to conf


    def initPlugins(self):
        self.accounts = {}  #: key = ( plugin )
        self.plugins = {}

        self.initAccountPlugins()
        self.loadAccounts()


    def getAccountPlugin(self, plugin):
        """Get account instance for plugin or None if anonymous"""
        try:
            if plugin in self.accounts:
                if plugin not in self.plugins:
                    klass = self.core.pluginManager.loadClass("accounts", plugin)
                    if klass:
                        self.plugins[plugin] = klass(self, self.accounts[plugin])
                    else:  #@NOTE: The account class no longer exists (blacklisted plugin). Skipping the account to avoid crash
                        raise

                return self.plugins[plugin]
            else:
                raise
        except Exception:
            return None


    def getAccountPlugins(self):
        """Get all account instances"""

        plugins = []
        for plugin in self.accounts.keys():
            plugins.append(self.getAccountPlugin(plugin))

        return plugins


    #----------------------------------------------------------------------

    def loadAccounts(self):
        """Loads all accounts available"""

        try:
            with open("accounts.conf", "a+") as f:
                content = f.readlines()
                version = content[0].split(":")[1].strip() if content else ""

                if not version or int(version) < ACC_VERSION:
                    shutil.copy("accounts.conf", "accounts.backup")
                    f.seek(0)
                    f.write("version: " + str(ACC_VERSION))

                    self.core.log.warning(_("Account settings deleted, due to new config format"))
                    return

        except IOError, e:
            self.core.log.error(str(e))
            return

        plugin = ""
        name = ""

        for line in content[1:]:
            line = line.strip()

            if not line:
                continue
            if line.startswith("#"):
                continue
            if line.startswith("version"):
                continue

            if line.endswith(":") and line.count(":") == 1:
                plugin = line[:-1]
                self.accounts[plugin] = {}

            elif line.startswith("@"):
                try:
                    option = line[1:].split()
                    self.accounts[plugin][name]['options'][option[0]] = [] if len(option) < 2 else ([option[1]] if len(option) < 3 else option[1:])
                except Exception:
                    pass

            elif ":" in line:
                name, sep, pw = line.partition(":")
                self.accounts[plugin][name] = {"password": pw, "options": {}, "valid": True}


    #----------------------------------------------------------------------

    def saveAccounts(self):
        """Save all account information"""

        try:
            with open("accounts.conf", "wb") as f:
                f.write("version: " + str(ACC_VERSION) + "\n")

                for plugin, accounts in self.accounts.iteritems():
                    f.write("\n")
                    f.write(plugin + ":\n")

                    for name, data in accounts.iteritems():
                        f.write("\n\t%s:%s\n" % (name, data['password']) )
                        if data['options']:
                            for option, values in data['options'].iteritems():
                                f.write("\t@%s %s\n" % (option, " ".join(values)))

            try:
                os.chmod(f.name, 0600)
            except Exception:
                pass

        except Exception, e:
            self.core.log.error(str(e))


    #----------------------------------------------------------------------

    def initAccountPlugins(self):
        """Init names"""
        for name in self.core.pluginManager.getAccountPlugins():
            self.accounts[name] = {}


    @lock
    def updateAccount(self, plugin, user, password=None, options={}):
        """Add or update account"""
        if plugin in self.accounts:
            p = self.getAccountPlugin(plugin)
            updated = p.updateAccounts(user, password, options)
            # since accounts is a ref in plugin self.accounts doesnt need to be updated here

            self.saveAccounts()
            if updated: p.scheduleRefresh(user, force=False)


    @lock
    def removeAccount(self, plugin, user):
        """Remove account"""

        if plugin in self.accounts:
            p = self.getAccountPlugin(plugin)
            p.removeAccount(user)

            self.saveAccounts()


    @lock
    def getAccountInfos(self, force=True, refresh=False):
        data = {}

        if refresh:
            self.core.scheduler.addJob(0, self.core.accountManager.getAccountInfos)
            force = False

        for p in self.accounts.keys():
            if self.accounts[p]:
                p = self.getAccountPlugin(p)
                if p:
                    data[p.__class__.__name__] = p.getAllAccounts(force)
                else:  #@NOTE: When an account has been skipped, p is None
                    data[p] = []
            else:
                data[p] = []
        e = AccountUpdateEvent()
        self.core.pullManager.addEvent(e)
        return data


    def sendChange(self):
        e = AccountUpdateEvent()
        self.core.pullManager.addEvent(e)
