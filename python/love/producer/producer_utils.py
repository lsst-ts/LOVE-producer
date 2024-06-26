# This file is part of LOVE-producer.
#
# Developed for the Rubin Observatory Telescope and Site System.
# This product includes software developed by Inria Chile and
# the LSST Project (https://www.lsst.org).
#
# See the COPYRIGHT file at the top-level directory of this distribution
# for details of code ownership and dependencies.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import json
import os
import re

import numpy as np
from lsst.ts import idl


def get_available_components():
    """Return a list of all CSCs available in the idl directory.

    Returns
    -------
    `set` of `str`
        CSCs with idl files in the idl directory.
    """
    pattern_match = re.compile("sal_revCoded_(.*)")

    return {
        pattern_match.findall(idl_files.stem)[0]
        for idl_files in idl.get_idl_dir().glob("*.idl")
        if pattern_match.match(idl_files.stem) is not None
    }


class Settings:
    _trace = None
    _ws_host = None
    _ws_pass = None

    @staticmethod
    def trace_timestamps():
        if Settings._trace is None:
            if os.environ.get("HIDE_TRACE_TIMESTAMPS", False):
                Settings._trace = False
            else:
                Settings._trace = True
        return Settings._trace

    @staticmethod
    def ws_host():
        if Settings._ws_host is None:
            Settings._ws_host = os.environ.get("WEBSOCKET_HOST", "0.0.0.0:9999")
        return Settings._ws_host

    @staticmethod
    def ws_pass():
        if Settings._ws_pass is None:
            Settings._ws_pass = os.environ.get("PROCESS_CONNECTION_PASS", "")
        return Settings._ws_pass

    @staticmethod
    def config_path():
        return "config/config.json"


class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (np.bool, np.bool_)):
            return bool(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(
            obj,
            (np.uint8, np.int16, np.int32, np.int64, np.uint8, np.uint16, np.uint32),
        ):
            return int(obj)
        return json.JSONEncoder.default(self, obj)


class MissingMessageParameterError(Exception):
    """Exception class to be raised on missing message parameter"""

    pass


class MissingMessageStreamError(Exception):
    """Exception class to be raised on missing message stream"""

    pass


class ConnectedTaskDoneError(Exception):
    """Exception raised by the LoveManagerclient.connect_to_manager method
    internally to handle condition where the connection to the manager was
    closed unexpectedly.
    """

    pass


def get_data_type(value):
    if isinstance(value, (np.ndarray)) and value.ndim == 0:
        return "Array<%s>" % get_data_type(value.item())

    if isinstance(value, (list, tuple, np.ndarray)):
        return "Array<%s>" % get_data_type(value[0])
    if isinstance(value, (int, np.integer)):
        return "Int"
    if isinstance(value, float):
        return "Float"
    if isinstance(value, str):
        return "String"
    return "None"


def onemsg_generator(category, csc, salindex, streams_dict):
    """Generates one msg for the LOVE-manager from a single (csc,salindex)
    source.
    """

    return {
        "category": category,
        "data": [
            {
                "csc": csc,
                "salindex": salindex,
                "data": json.loads(json.dumps(streams_dict, cls=NumpyEncoder)),
            }
        ],
    }


def get_stream_from_last_message(message, category, csc, salindex, stream):
    """
    Takes a message and returns a parameter for a given (category, csc,
    salindex,stream). If not found then it will throw an error.
    """
    if message["category"] != category:
        return
    for m in message["data"]:
        if m["csc"] == csc and m["salindex"] == salindex:
            return m["data"][stream]

    raise MissingMessageStreamError(
        "Stream {}-{}-{}-{} not found in message".format(
            category, csc, salindex, stream
        )
    )


def check_stream_from_last_message(message, category, csc, salindex, stream):
    """
    Takes a message and returns a parameter for a given (category, csc,
    salindex,stream). If not found then it will throw an error.
    """
    if message["category"] != category:
        return False
    for m in message["data"]:
        if m["csc"] == csc and int(m["salindex"]) == int(salindex):
            return True

    return False


def get_parameter_from_last_message(
    message, category, csc, salindex, stream, parameter
):
    """
    Takes a message and returns a parameter for a given (category, csc,
    salindex, stream). If not found then it will throw an error.
    """
    if message["category"] != category:
        return
    for m in message["data"]:
        if m["csc"] == csc and m["salindex"] == salindex:
            return m["data"][stream][parameter]

    raise MissingMessageParameterError(
        "Parameter {}-{}-{}-{}-{} not found in message".format(
            category, csc, salindex, stream, parameter
        )
    )


def get_all_csc_names_in_message(message):
    """
    Returns a list of all cscs names contained in a message
    """
    return [data["csc"] for data in message["data"]]


def get_event_stream(message, category, csc, salindex, stream_name):
    """Tries to return the first stream found in a LOVE message.
    Throws errors if it does not exist."""

    data_generator = (
        d for d in message["data"] if d["csc"] == csc and d["salindex"] == salindex
    )
    data = next(data_generator)
    stream_generator = (data["data"][s] for s in data["data"] if s == stream_name)
    stream = next(stream_generator)
    return stream


def check_event_stream(message, category, csc, salindex, stream_name):
    """Tries to return the first stream found in a LOVE message.
    Throws errors if it does not exist."""

    try:
        data_generator = (
            d for d in message["data"] if d["csc"] == csc and d["salindex"] == salindex
        )
        data = next(data_generator)
    except StopIteration:
        return False
    except KeyError:
        return False

    stream_generator = (data["data"][s] for s in data["data"] if s == stream_name)

    try:
        next(stream_generator)
        return True
    except StopIteration:
        return False


def make_stream_message(category, csc, salindex, stream, content):
    """Returns a message for the LOVE-manager group
    (category-csc-salindex-stream) with a given content.
    """

    return {
        "category": category,
        "data": [
            {
                "csc": csc,
                "salindex": salindex,
                "data": {stream: [content] if category == "event" else content},
            }
        ],
    }
