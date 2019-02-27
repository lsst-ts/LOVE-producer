from request_model import RequestModel

class ScriptProducer:
    __init__(self):

    self.queue = RequestModel(1)
    state = self.queue.get_queue_state()
    print(state)