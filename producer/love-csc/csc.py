import argparse
import asyncio
import sys
import warnings

# from . import base
# from .sal_enums import State
# from .controller import Controller

from lsst.ts import salobj

HEARTBEAT_INTERVAL = 1  # seconds


class LOVECsc(salobj.Controller):
    """Base class for a Commandable SAL Component (CSC)

    To implement a CSC in Python define a subclass of this class.

    Parameters
    ----------
    name : `str`
        Name of SAL component.
    index : `int` or `None`
        SAL component index, or 0 or None if the component is not indexed.
    initial_state : `State` or `int` (optional)
        The initial state of the CSC. This is provided for unit testing,
        as real CSCs should start up in `State.STANDBY`, the default.
    simulation_mode : `int` (optional)
        Simulation mode. The default is 0: do not simulate.
    initial_simulation_mode : `int` (optional)
        A deprecated synonym for simulation_mode.

    Raises
    ------
    ValueError
        If ``initial_state`` is invalid, or
        ``simulation_mode`` and ``initial_simulation_mode`` are both nonzero.
    salobj.ExpectedError
        If ``simulation_mode`` is invalid.
        Note: you will only see this error if you await `start_task`.


    Notes
    -----
    **Attributes**

    * ``heartbeat_interval``: interval between heartbeat events, in seconds;
      a `float`.

    **Constructor**

    The constructor does the following, beyond the parent class constructor:

    * For each command defined for the component, find a ``do_<name>`` method
      (which must be present) and add it as a callback to the
      ``cmd_<name>`` attribute.
    * The base class provides asynchronous ``do_<name>`` methods for the
      standard CSC commands. The default implementation is as follows
      (if any step fails then the remaining steps are not performed):

        * Check for validity of the requested state change;
          if the change is valid then:
        * Call ``begin_<name>``. This is a no-op in the base class,
          and is available for the subclass to override. If this fails,
          then log an error and acknowledge the command as failed.
        * Change self.summary_state.
        * Call ``end_<name>``. Again, this is a no-op in the base class,
          and is available for the subclass to override.
          If this fails then revert ``self.summary_state``, log an error,
          and acknowledge the command as failed.
        * Call `handle_summary_state` and `report_summary_state`
          to handle report the new summary state.
          If this fails then leave the summary state updated
          (since the new value *may* have been reported),
          but acknowledge the command as failed.
        * Acknowledge the command as complete.

    * Set the summary state.
    * Run `start` asynchronously.
    """
    def __init__(self):
        super().__init__(name='LOVE', index=None, do_callbacks=False)
        self.heartbeat_interval = HEARTBEAT_INTERVAL

    def observing_log(self, user, message):
        """Add message to observing log"""
        self.evt_observingLog.set(user=user, message=message)
        self.evt_observingLog.put()
