# -*- coding: utf-8 -*-

from __future__ import with_statement

from os import path
from gettext import gettext
from collections import OrderedDict, namedtuple

from pyload.config import convert, default
from pyload.utils import chmod, encode

__all__ = ["ConfigParser", "Section"]

SectionTuple = namedtuple("SectionTuple", "label description explanation config")


class ConfigParser:
    """Holds and manages the configuration + meta data for config read from file"""

    CONFIG = "pyload.conf"

    def __init__(self, config=None):
        if config:
            self.CONFIG = config

        # Meta data information
        self.config = OrderedDict()
        # The actual config values
        self.values = {}

        self.checkVersion()

        self.loadDefault()
        self.parseValues(self.CONFIG)


    def loadDefault(self):
        default.make_config(self)


    def checkVersion(self):
        """Determines if config needs to be deleted"""
        if path.exists(self.CONFIG):
            f = open(self.CONFIG, "rb")
            v = f.readline()
            f.close()
            v = v[v.find(":") + 1:].strip()

            if not v or int(v) < CONF_VERSION:
                f = open(self.CONFIG, "wb")
                f.write("version: " + str(CONF_VERSION))
                f.close()
                print "Old version of %s deleted" % self.CONFIG
        else:
            f = open(self.CONFIG, "wb")
            f.write("version:" + str(CONF_VERSION))
            f.close()


    def parseValues(self, filename):
        """Read config values from file"""
        f = open(filename, "rb")
        config = f.readlines()[1:]

        # save the current section
        section = ""

        for line in config:
            line = line.strip()

            # comment line, different variants
            if not line or line.startswith("#") \
                        or line.startswith("//") \
                        or line.startswith(";"):
                continue

            if line.startswith("["):
                section = line.replace("[", "").replace("]", "")

                if section not in self.config:
                    print "Unrecognized section", section
                    section = ""

            else:
                name, non, value = line.rpartition("=")
                name = name.strip()
                value = value.strip()

                if not section:
                    print "Value without section", name
                    continue

                if name in self.config[section].config:
                    self.set(section, name, value, sync=False)
                else:
                    print "Unrecognized option", section, name


    def save(self):
        """Saves config to filename"""

        configs = []
        f = open(self.CONFIG, "wb")
        configs.append(f)
        chmod(self.CONFIG, 0600)
        f.write("version: %i\n\n" % CONF_VERSION)

        for section, data in self.config.iteritems():
            f.write("[%s]\n" % section)

            for option, data in data.config.iteritems():
                value = encode(self.get(section, option))

                f.write('%s = %s\n' % (option, value))

            f.write("\n")

        f.close()


    def __getitem__(self, section):
        """Provides dictionary like access: c['section']['option']"""
        return Section(self, section)


    def __contains__(self, section):
        """Checks if parser contains section"""
        return section in self.config


    def get(self, section, option):
        """Get value or default"""
        try:
            return self.values[section][option]
        except KeyError:
            return self.config[section].config[option].input.default_value


    def set(self, section, option, value, sync=True):
        """Set value"""

        data = self.config[section].config[option]
        value = convert.from_string(value, data.input.type)
        old_value = self.get(section, option)

        # only save when different values
        if value != old_value:
            if section not in self.values:
                self.values[section] = {}
            self.values[section][option] = value
            if sync:
                self.save()
            return True

        return False


    def getMetaData(self, section, option):
        """Get all config data for an option"""
        return self.config[section].config[option]


    def iterSections(self):
        """Yields section, config info, values, for all sections"""
        for name, config in self.config.iteritems():
            yield name, config, self.values[name] if name in self.values else {}


    def getSection(self, section):
        """Retrieves single config as tuple (section, values)"""
        return self.config[section], self.values[section] if section in self.values else {}


    def addConfigSection(self, section, label, desc, expl, config):
        """
        Adds a section to the config. `config` is a list of config tuple as used in plugin api defined as:
        The order of the config elements is preserved with OrderedDict
        """
        d = OrderedDict()

        for entry in config:
            name, data = convert.to_configdata(entry)
            d[name] = data

        data = SectionTuple(gettext(label), gettext(desc), gettext(expl), d)
        self.config[section] = data


class Section:
    """Provides dictionary like access for configparser"""

    def __init__(self, parser, section):
        """Constructor"""
        self.parser = parser
        self.section = section


    def __getitem__(self, item):
        """Getitem"""
        return self.parser.get(self.section, item)


    def __setitem__(self, item, value):
        """Setitem"""
        self.parser.set(self.section, item, value)
