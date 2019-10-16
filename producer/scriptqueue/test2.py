import asyncio
import unittest
import asynctest
import warnings

from lsst.ts import salobj
from lsst.ts import scriptqueue
from lsst.ts.idl.enums.ScriptQueue import ScriptProcessState
from lsst.ts.idl.enums.Script import ScriptState
import os
import yaml
from .producer import ScriptQueueProducer
from unittest.mock import MagicMock
from lsst.ts.idl.enums.ScriptQueue import Location
import utils
STD_TIMEOUT = 10
START_TIMEOUT = 20
END_TIMEOUT = 10


class QueueTestCase(asynctest.TestCase):
    async def setUp(self):
        self.domain = salobj.Domain()
        self.remote = salobj.Remote(self.domain, 'ScriptQueue', 1)

    async def tearDown(self):
        nkilled = len(self.model.terminate_all())
        if nkilled > 0:
            warnings.warn(f"Killed {nkilled} subprocesses")

        await self.domain.close()

    async def assert_next_queue(self, enabled=True, running=False, current_sal_index=0,
                                sal_indices=(), past_sal_indices=(), wait=False):
        """
        Adapted from https://github.com/lsst-ts/ts_scriptqueue/blob/77c6a1881f1e5d6bf1840cbce096e492ff54abfe/tests/test_queue_model.py
        
        Assert that the queue is in a particular state.
        If wait is True then wait for the next update before checking.
        The defaults are appropriate to an enabled, paused queue
        with no scripts.
        Parameters
        ----------
        enabled : `bool`
            Is the queue enabled?
        running : `bool`
            Is the queue running?
        current_sal_index : `int`
            SAL index of current script, or 0 if no current script.
        sal_indices : ``sequence`` of `int`
            SAL indices of scripts on the queue.
        past_sal_indices : ``sequence`` of `int`
            SAL indices of scripts in history.
        wait : `bool`
            If True then wait for queue_task.
        """
        if wait:
            await asyncio.wait_for(self.queue_task, 60)
        self.assertEqual(self.model.running, running)
        self.assertEqual(self.model.current_index, current_sal_index)
        self.assertEqual([info.index for info in self.model.queue], list(sal_indices))
        self.assertEqual([info.index for info in self.model.history], list(past_sal_indices))
        self.queue_task = asyncio.Future()
        
    async def test_update(self):
        # Add a script to the queue and wait until it finishes and pause its

        ack = await self.remote.cmd_add.set_start(isStandard=True,
                                            path="script1",
                                            config="wait_time: 0.1",
                                            location=Location.LAST,
                                            locationSalIndex=0,
                                            descr="test_add", timeout=5)

        script_index = int(ack.result)
        script_remote = salobj.Remote(self.queue.domain, 'Script', script_index)

    
        self.assert_next_queue(enabled=True, running=)