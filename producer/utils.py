import numpy as np
import json


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