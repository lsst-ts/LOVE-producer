import numpy as np
import json
import os

CONFIG_PATH = 'config/config.json'
WS_HOST = ""
if "WEBSOCKET_HOST" in os.environ:
    WS_HOST = os.environ["WEBSOCKET_HOST"]

WS_PASS = ""
if "PROCESS_CONNECTION_PASS" in os.environ:
    WS_PASS = os.environ["PROCESS_CONNECTION_PASS"]


class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (np.bool, np.bool_)):
            return bool(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, (np.uint8, np.int16, np.int32, np.int64, np.uint8, np.uint16, np.uint32)):
            return int(obj)
        return json.JSONEncoder.default(self, obj)


def getDataType(value):
    if isinstance(value, (np.ndarray)) and value.ndim == 0:
        return 'Array<%s>' % getDataType(value.item())

    if isinstance(value, (list, tuple, np.ndarray)):
        return 'Array<%s>' % getDataType(value[0])
    if isinstance(value, (int, np.integer)):
        return 'Int'
    if isinstance(value, float):
        return 'Float'
    if isinstance(value, str):
        return 'String'
    return 'None'


def onemsg_generator(category, csc, salindex, streamsDict):
    """Generates one msg for the LOVE-manager from a single (csc,salindex) source """

    return {
        'category': category,
        'data': [
            {
                'csc': csc,
                'salindex': salindex,
                'data': json.loads(json.dumps(streamsDict, cls=NumpyEncoder))
            }
        ]
    }


def get_stream_from_last_message(message, category, csc, salindex, stream):
    """
    Takes a message and returns a parameter for a given (category,csc,salindex,stream) 
    If not found then it will throw an error
    """
    if message['category'] != category:
        return
    for m in message['data']:
        if m['csc'] == csc and m['salindex'] == salindex:
            return m['data'][stream]

    raise Exception('Stream {}-{}-{}-{} not found in message'.format(category, csc, salindex, stream))


def check_stream_from_last_message(message, category, csc, salindex, stream):
    """
    Takes a message and returns a parameter for a given (category,csc,salindex,stream) 
    If not found then it will throw an error
    """
    if message['category'] != category:
        return False
    for m in message['data']:
        if m['csc'] == csc and int(m['salindex']) == int(salindex):
            return True

    return False


def get_parameter_from_last_message(message, category, csc, salindex, stream, parameter):
    """
    Takes a message and returns a parameter for a given (category,csc,salindex,stream) 
    If not found then it will throw an error
    """
    if message['category'] != category:
        return
    for m in message['data']:
        if m['csc'] == csc and m['salindex'] == salindex:
            return m['data'][stream][parameter]

    raise Exception('Parameter {}-{}-{}-{}-{} not found in message'.format(category, csc, salindex, stream, parameter))


def get_all_csc_names_in_message(message):
    """
        Returns a list of all cscs names contained in a message
    """
    return [data['csc'] for data in message['data']]


def get_event_stream(message, category, csc, salindex, stream_name):
    """ Tries to return the first stream found in a LOVE message. 
    Throws errors if it does not exist. """

    data_generator = (d for d in message['data'] if d["csc"] == csc and d['salindex'] == salindex)
    data = next(data_generator)
    stream_generator = (data['data'][s] for s in data['data'] if s == stream_name)
    stream = next(stream_generator)
    return stream


def check_event_stream(message, category, csc, salindex, stream_name):
    """ Tries to return the first stream found in a LOVE message. 
    Throws errors if it does not exist. """

    data_generator = (d for d in message['data'] if d["csc"] == csc and d['salindex'] == salindex)
    try:
        data = next(data_generator)
    except StopIteration:
        return False

    stream_generator = (data['data'][s] for s in data['data'] if s == stream_name)

    try:
        next(stream_generator)
        return True
    except StopIteration:
        return False


def make_stream_message(category, csc, salindex, stream, content):
    """Returns a message for the LOVE-manager group (category-csc-salindex-stream) with 
    a given content """

    return {
        "category": category,
        "data": [{
            'csc': csc,
            'salindex': salindex,
            'data': {
                stream: [content] if category == 'event' else content
            }
        }]
    }
