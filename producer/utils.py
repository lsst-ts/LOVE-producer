import numpy as np
import json
import os

CONFIG_PATH = 'config/config.json'
WS_HOST = os.environ["WEBSOCKET_HOST"]
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


def read_config(path, key=None):
    """ Reads a given config file and returns the lists of CSCs to listen to.
    It can read the full file (by default), or read only a specific key

    Parameters
    ----------
    path: `string`
        The full path of the config file
    key: `string`
        optional key to read

    Returns
    -------
    csc_list: `[()]`
        The list of CSCs to run as a tuple with the CSC name and index
    """
    print('Reading config file: ', path)
    with open(path) as config_file:
        data = json.loads(config_file.read())

    # data = json.load(open(path, 'r'))
    csc_list = []
    if key:
        for csc_instance in data[key]:
            index = 0
            if 'index' in csc_instance:
                index = csc_instance['index']
            csc_list.append((key, index))
    else:
        for csc_key, csc_value in data.items():
            for csc_instance in csc_value:
                index = 0
                if 'index' in csc_instance:
                    index = csc_instance['index']
                csc_list.append((csc_key, index))
    return csc_list
