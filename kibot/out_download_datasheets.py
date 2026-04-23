# -*- coding: utf-8 -*-
# Copyright (c) 2021-2026 Salvador E. Tropea
# Copyright (c) 2021-2026 Instituto Nacional de Tecnología Industrial
# License: AGPL-3.0
# Project: KiBot (formerly KiPlot)
"""
Dependencies:
  - name: Curl
    role: Download datasheets
    url: https://curl.se/
    debian: curl
    arch: curl
"""
import os
import re
import requests
from subprocess import CalledProcessError
import urllib.request
from .optionable import Optionable
from .out_base import VariantOptions
from .fil_base import DummyFilter
from .error import KiPlotConfigurationError
from .kiplot import run_command
from .misc import W_UNKFLD, W_ALRDOWN, W_FAILDL, USER_AGENT
from .gs import GS
from .macros import macros, document, output_class  # noqa: F401
from . import log
logger = log.get_logger()
SUBDIRS = {'C': 'Capacitors', 'R': 'Resistors', 'L': 'Inductors', 'U': 'Integrated_Circuits', 'J': 'Connectors',
           'D': 'Diodes', 'Q': 'Transistors', 'Y': 'Crystals', 'BZ': 'Buzzers', 'FL': 'Filters', 'JP': 'Jumpers',
           'M': 'Motors', 'K': 'Relays', 'HS': 'Heat_Sinks', 'F': 'Fuses', 'AE': 'Antennas'}


def is_url(ds):
    return ds.startswith('http://') or ds.startswith('https://')


class Download_Datasheets_Options(VariantOptions):
    _vars_regex = re.compile(r'\$\{([^\}]+)\}')

    def __init__(self):
        super().__init__()
        with document:
            self.field = 'Datasheet'
            """ *Name of the field containing the URL """
            self.output = '${VALUE}.pdf'
            """ Name used for the downloaded datasheet.
                `${FIELD}` will be replaced by the FIELD content """
            self.classify = False
            """ Use the reference to classify the components in different sub-dirs.
                In this way C7 will go into a Capacitors sub-dir, R3 into Resistors, etc """
            self.classify_extra = Optionable
            """ [string_dict={}] Extra reference associations used to classify the references.
                They are pairs `Reference prefix` -> `Sub-dir` """
            self.dnf = False
            """ Include the DNF components """
            self.repeated = False
            """ Download URLs that we already downloaded.
                It only makes sense if the `output` field makes their output different """
            self.link_repeated = True
            """ Instead of download things we already downloaded use symlinks """
        # Used to collect the targets
        self._dry = False
        self._unknown_is_error = True
        self._curl_command = None   # We detect it on `run`

    def config(self, parent):
        super().config(parent)
        if not self.field:
            raise KiPlotConfigurationError("Empty `field` ({})".format(str(self._tree)))
        if not self.output:
            raise KiPlotConfigurationError("Empty `output` ({})".format(str(self._tree)))
        self.field = self.field.lower()

    def do_warning(self, msg, ds, c):
        logger.warning(W_FAILDL+'{} during download of `{}` [{}]'.format(msg, ds, c.ref))
        return None

    def validate_downloaded(self, file):
        if not os.path.isfile(file):
            # Not there
            logger.debug("- Download command succeed, but no downloaded file")
            return False
        if os.path.getsize(file) == 0:
            # Empty
            os.remove(file)
            logger.debug("- Empty file downloaded, removing it")
            return False
        if os.path.splitext(file)[1].lower() != ".pdf":
            # There, not empty and not a PDF
            return True
        # Test for PDF and not a web page
        try:
            with open(file, 'rb') as f:
                header = f.read(4)
        except Exception as e:
            # Failed to read it
            logger.debug("- Downloaded file can't be read "+str(e))
            return False
        if header != b'%PDF':
            # Not a PDF, remove it
            os.remove(file)
            logger.debug("- Downloaded file isn't a PDF")
            return False
        return True

    def download(self, c, ds, dir, name, known):
        if self.classify:
            subdir = self.classify_extra.get(c.ref_prefix, SUBDIRS.get(c.ref_prefix, 'Miscellaneous'))
            os.makedirs(os.path.join(dir, subdir), exist_ok=True)
            name = os.path.join(subdir, name)
        dest = os.path.join(dir, name)
        logger.debug('To download: {} -> {}'.format(ds, dest))
        if name in self._downloaded:
            logger.warning(W_ALRDOWN+'Datasheet `{}` already downloaded'.format(name))
            return None
        elif known is not None and self.link_repeated:
            # We already downloaded this URL, but stored it with a different name
            if not self._dry:
                os.symlink(known, dest)
            self._created.append(os.path.relpath(dest))
        elif not os.path.isfile(dest):
            # Download
            if not self._dry:
                downloaded = False
                if self._curl_command:
                    # Using curl
                    cmd = [self._curl_command, '-o', dest, ds]
                    try:
                        run_command(cmd, just_raise=True)
                        downloaded = self.validate_downloaded(dest)
                    except CalledProcessError as e:
                        logger.warning(W_FAILDL+f'Failed to download {ds} using {self._curl_command} ({e})')
                if not downloaded:
                    # Using Python's request
                    if 'digikey' in ds:
                        req = urllib.request.Request(ds)
                        req.add_header('User-Agent', USER_AGENT)
                        try:
                            data = urllib.request.urlopen(req).read()
                        except Exception as e:
                            return self.do_warning('Failed '+str(e), ds, c)
                    else:
                        try:
                            r = requests.get(ds, allow_redirects=True, headers={'User-Agent': USER_AGENT}, timeout=20)
                        except requests.exceptions.ReadTimeout:
                            return self.do_warning('Timeout', ds, c)
                        except requests.exceptions.SSLError:
                            return self.do_warning('SSL Error', ds, c)
                        except requests.exceptions.TooManyRedirects:
                            return self.do_warning('More than 30 redirections', ds, c)
                        except requests.exceptions.ConnectionError:
                            return self.do_warning('Connection', ds, c)
                        except requests.exceptions.RequestException as e:
                            return self.do_warning(str(e), ds, c)
                        if r.status_code != 200:
                            return self.do_warning('Failed with status '+str(r.status_code), ds, c)
                        else:
                            data = r.content
                    with open(dest, 'wb') as f:
                        f.write(data)
            self._downloaded.add(name)
            self._created.append(os.path.relpath(dest))
        elif self._dry:
            self._created.append(os.path.relpath(dest))
        return name

    def out_name(self, c):
        """ Compute the name of the output file.
            Replaces `${FIELD}` and %X. """
        out = ''
        last = 0
        pattern = self.output
        pattern_l = len(pattern)
        for match in Download_Datasheets_Options._vars_regex.finditer(pattern):
            fname = match.group(1).lower()
            value = c.get_field_value(fname)
            if value is None:
                value = 'Unknown'
                logger.warning(W_UNKFLD+"In datasheets download output file name:"
                               " Field `{}` not defined for {}, using `Unknown`".format(fname, c.ref))
            if match.start():
                out += pattern[last:match.start()]
            out += value
            last = match.end()
        if last < pattern_l:
            out += pattern[last:pattern_l]
        out = self.expand_filename_sch(out)
        return out.replace('/', '_')

    def run(self, output_dir):
        if not self.dnf_filter and not self.variant:
            # Add a dummy filter to force the creation of a components list
            self.dnf_filter = DummyFilter()
        super().run(output_dir)
        self._curl_command = self.check_tool('Curl')
        self._urls = {}
        self._downloaded = set()
        self._created = []
        field_used = False
        for c in self._comps:
            ds = c.get_field_value(self.field)
            if ds is not None:
                field_used = True
            if not c.included or (not c.fitted and not self.dnf):
                continue
            if ds and is_url(ds):
                known = self._urls.get(ds, None)
                if known is None or self.repeated:
                    name = self.out_name(c)  # Here to simplify the tests
                    name = self.download(c, ds, output_dir, name, known)
                    if known is None:
                        self._urls[ds] = name
                else:
                    logger.debug('Already downloaded: '+ds)
        if not field_used:
            known_fields = GS.sch.get_field_names({})
            if self.field not in known_fields:
                logger.warning(W_UNKFLD+"The field used for datasheets ({}) doesn't seem to be used".format(self.field))
        else:
            logger.debug('Unique URLs: '+str(len(self._urls)))
            logger.debug('Downloaded: '+str(len(self._downloaded)))
            logger.debug('Created: '+str(len(self._created)))

    def get_targets(self, out_dir):
        # Do a dry run to collect the output names
        self._dry = True
        self.run(out_dir)
        self._dry = False
        return self._created


@output_class
class Download_Datasheets(BaseOutput):  # noqa: F821
    """ Datasheets downloader
        Downloads the datasheets for the project """
    def __init__(self):
        super().__init__()
        with document:
            self.options = Download_Datasheets_Options
            """ *[dict={}] Options for the `download_datasheets` output """
        self._sch_related = True
        self._category = 'Schematic/docs'

    def run(self, output_dir):
        # No output member, just a dir
        self.options.run(output_dir)

    @staticmethod
    def get_conf_examples(name, layers):
        has_urls = False
        for c in GS.sch.get_components():
            if c.datasheet and is_url(c.datasheet):
                has_urls = True
                break
        if not has_urls:
            return None
        return BaseOutput.simple_conf_examples(name, 'Download the datasheets', 'Datasheets')  # noqa: F821
