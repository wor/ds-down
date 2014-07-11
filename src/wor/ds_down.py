#!/usr/bin/env python3
# -*- coding: utf-8 -*- vim:fenc=utf-8:ft=python:et:sw=4:ts=4:sts=4
#
# Copyright (C) 2014 Esa Määttä
#
# This file is part of ds-down.
#
# ds-down is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# ds-down is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with ds-down.  If not, see <http://www.gnu.org/licenses/>.
"""Synology Download Station url adder.
"""

import sys
import os
import logging
import requests
import json
import configparser
import subprocess


class NoDefaultHeaderConfigParser(configparser.ConfigParser):
    """ConfigParser without the need of default section."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.base_config_name = "BASE_CONFIG_98f93"
    def read_file(self, f, source=None):
        def no_default_header_config_file(config_file):
            """Generator which wraps config_file and gives DEFAULT section header as
            the first line.

            Parameters:
                config_file: file like object. Open config file.
            """
            # As DEFAULT is included in all other sections when reading
            # items/options add empty DEFAULT section and use BASE as base config
            # section.
            yield "[DEFAULT]\n"
            yield "[" + self.base_config_name + "]\n"
            # Next yield the actual config file next
            for line in config_file:
                yield line
        return super().read_file(no_default_header_config_file(f), source)
    def get_default(self, option, *args, **kwargs):
        """Gets an option from the default context."""
        return super().get(self.base_config_name, option, *args, **kwargs)

def get_password(cmd):
    """Gets pasword from given console commands output.

    The password is the outputs last line without the end of line marker.

    Returns:
        str | None. Password or None in case of an error.

    Parameters:
        cmd: str. Command to be executed in a subprocess for the password.
    """
    log = logging.getLogger(__name__)

    if not cmd:
        return None
    cmd_split = [os.path.expanduser(p) for p in cmd.split()]
    try:
        output = str(subprocess.check_output(cmd_split), encoding='utf-8')
    except subprocess.CalledProcessError as e:
        emsg = "Error: could not get password with command: {} (exit status: {})\n{}".format(
                cmd_split, e.returncode, e.output)
        # Add line separator if missing so that possible additional output is clearer
        if emsg[-1] != os.linesep:
            emsg += os.linesep
        log.error(emsg)
        return None

    # Select last line as password from the output and remove any line
    # separators from the end.
    password = output.rstrip(os.linesep).rpartition(os.linesep)[2]
    if not password: # No empty passwords
        return None
    return password

def read_config(config_fn):
    """Reads (parses) given config file.

    Returns:
        (str|None, str|None, str|None). Username, host, password 3-tuple.

    Parameters:
        config_fn: str. Config file name (path).
    """
    log = logging.getLogger(__name__)
    def get_option(opt_name):
        try:
            return config.get_default(opt_name)
        except configparser.NoOptionError as e:
            log.error("Config file did not contain value for '{}'.".format(opt_name))
        return None

    config = NoDefaultHeaderConfigParser()
    config_fn = os.path.expanduser(config_fn)

    # Parse config file to the config
    if os.path.exists(config_fn):
        with open(config_fn) as cf:
            config.read_file(cf, source=config_fn)
    else:
        log.error("Could not open config file: {}".format(config_fn))
        return None, None, None

    username     = get_option("username")
    host         = get_option("host")
    password     = get_password(get_option("passwordeval"))
    return username, host, password

def send_url(add_url, config_file):
    """Sends the given url Synology DownloadStation.

    Now handles only local files and urls which start with "http:"
    """
    log = logging.getLogger(__name__)
    log.debug("Using config file: {}".format(config_file))
    log.debug("Adding url: {}".format(add_url))

    username, host, password = read_config(config_file)
    if not username or not host or not password:
        return False

    host = host + "/webapi"
    url_auth = host + "/auth.cgi"
    url_ds = host + "/DownloadStation/task.cgi"

    # Init session and geth auth token
    data = {
        'api': 'SYNO.API.Auth',
        'version': '2',
        'method': 'login',
        'account': username,
        'passwd': password,
        'session': 'DownloadStation',
        'format': 'sid'
    }
    r = requests.post(url=url_auth, data=data, verify=False)
    if r.status_code != 200:
        log.error("Auth request failed with status code: {}",format(r.status_code))
        return False
    rj = json.loads(r.text)
    if not rj['success']:
        log.error("Auth failed with response data: {}".format(rj))
        return False
    auth = rj['data']['sid']

    session = requests.session() # XXX: is this only for cookie and not sid
    # Send local file
    if not add_url.startswith("http:") and not add_url.startswith("magnet:"):
        with open(add_url,'rb') as payload:
            args = {
                    'api': 'SYNO.DownloadStation.Task',
                    'version': '1',
                    'method': 'create',
                    'session': 'DownloadStation',
                    '_sid': auth
                    }
            files = {'file': (add_url, payload)}
            r = session.post(url_ds, data=args, files=files, verify=False)
            if r.status_code != 200:
                log.error("Add file request failed with status code: {}",format(r.status_code))
                return False
            rj = json.loads(r.text)
            if not rj['success']:
                log.error("Add file failed with response data: {}".format(rj))
                return False
    else:
        # Send the url
        data = {
            'api': 'SYNO.DownloadStation.Task',
            'version': '1',
            'method': 'create',
            'session': 'DownloadStation',
            '_sid': auth,
            'uri': add_url
        }
        r = session.post(url=url_ds, data=data, verify=False)
        if r.status_code != 200:
            log.error("Add uri request failed with status code: {}",format(r.status_code))
            return False
        rj = json.loads(r.text)
        if not rj['success']:
            log.error("Add uri failed with response data: {}".format(rj))
            return False

    # Logout
    data = {
        'api': 'SYNO.API.Auth',
        'version': '1',
        'method': 'logout',
        'session': 'DownloadStation',
    }
    r = session.post(url_auth, data=data, verify=False)
    if r.status_code != 200:
        log.error("Logout request failed with status code: {}",format(r.status_code))
        return False
    rj = json.loads(r.text)
    if not rj['success']:
        log.error("Logout failed with response data: {}".format(rj))
        return False

    return True


def process_cmd_line(inputs=sys.argv[1:], parent_parsers=list()):
    """
    Processes command line arguments.

    Returns a namespace with all arguments.

    Parameters:

    - inputs: List. List of arguments to be parsed.
    - parent_parsers: List. List of parent parsers which are used as base.
    """
    import argparse
    class Verbose_action(argparse.Action):
        """Argparse action: Cumulative verbose switch '-v' counter"""
        def __call__(self, parser, namespace, values, option_string=None):
            """Values can be None, "v", "vv", "vvv" or [0-9]+
            """
            if values is None:
                verbosity_level = 1
            elif values.isdigit():
                verbosity_level = int(values)
            else: # [v]+
                v_count = values.count('v')
                if v_count != len(values):
                    raise argparse.ArgumentError(self, "Invalid parameter given for verbose: '{}'".format(values))
                verbosity_level = v_count+1

            # Append to previous verbosity level, this allows multiple "-v"
            # switches to be cumulatively counted.
            verbosity_level += getattr(namespace, self.dest)
            setattr(namespace, self.dest, verbosity_level)
    class Quiet_action(argparse.Action):
        """Argparse action: Cumulative quiet switch '-q' counter"""
        def __call__(self, parser, namespace, values, option_string=None):
            """qalues can be None, "q", "qq", "qqq" or [0-9]+
            """
            if values is None:
                verbosity_level = 1
            elif values.isdigit():
                verbosity_level = int(values)
            else: # [q]+
                q_count = values.count('q')
                if q_count != len(values):
                    raise argparse.ArgumentError(self, "Invalid parameter given for quiet: '{}'".format(values))
                verbosity_level = q_count+1

            # Append to previous verbosity level, this allows multiple "-q"
            # switches to be cumulatively counted.
            verbosity_level = getattr(namespace, self.dest) - verbosity_level
            setattr(namespace, self.dest, verbosity_level)


    # initialize the parser object:
    parser = argparse.ArgumentParser(
            parents=parent_parsers,
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            description="""Passes urls and files to Synology DownloadStation for download.""")

    parser.add_argument(
        '-c', '--config-file',
        type=str,
        default="~/.config/ds-down.conf",
        help="Config file.")

    parser.add_argument(
        '-v',
        nargs='?',
        default=10,
        action=Verbose_action,
        dest='verbose',
        help="Verbosity level specifier.")

    parser.add_argument(
        '-q',
        nargs='?',
        action=Quiet_action,
        dest='verbose',
        help="Be more quiet, negatively affects verbosity level.")

    parser.add_argument(
        'add_url',
        metavar='DownloadURL',
        #nargs=1, # If defined then a list is produced
        help='URL to be passed to DownloadStation.')

    return parser.parse_args(inputs)


def main():
    """
    Main entry to the program when used from command line. Registers default
    signals and processes command line arguments from sys.argv.
    """
    import signal
    import wor.utils

    def term_sig_handler(signum, frame):
        """Handles terminating signal."""
        print()
        sys.exit(1)

    def convert_int_to_logging_level(verbosity_level):
        """Convert integer verbosity level from range [-2,2] to range [10,50]
        with step=10.

        Input:          -2, -1,  0,  1,  2
        Return value:   10, 20, 30, 40, 50

        Parameters:

        - `verbosity_level`: int. Verbosity level to convert.

        Example:

        >>> convert_int_to_logging_level(-10)
        50
        >>> convert_int_to_logging_level(-2)
        50
        >>> convert_int_to_logging_level(0)
        30
        >>> convert_int_to_logging_level(2)
        10
        >>> convert_int_to_logging_level(8)
        10
        """
        # Force input to range [-2,2]
        if verbosity_level > 2:
            verbosity_level = 2
        elif verbosity_level < -2:
            verbosity_level = -2

        return abs(verbosity_level-3)*10

    signal.signal(signal.SIGINT, term_sig_handler) # for ctrl+c

    args = process_cmd_line()

    # Init module level logger with given verbosity level
    lformat = '%(levelname)s:%(funcName)s:%(lineno)s: %(message)s'
    logging.basicConfig(
            level=convert_int_to_logging_level(args.verbose),
            format=lformat)

    del args.verbose

    return 0 if send_url(**args.__dict__) else 1
