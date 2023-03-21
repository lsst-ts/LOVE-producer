# This file is part of LOVE-producer.
#
# Developed for Vera C. Rubin Observatory Telescope and Site Systems.
# This product includes software developed by the LSST Project
# (https://www.lsst.org).
# See the COPYRIGHT file at the top-level directory of this distribution
# for details of code ownership.
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

__all__ = ["LoveProducerBase"]

import asyncio
import hashlib
import logging

from typing import (
    Any,
    Callable,
    Coroutine,
    List,
    Optional,
    Tuple,
    AsyncIterator,
)

from . import LoveManagerMessage


class LoveProducerBase:
    """Base class for Love Producer.

    This base class implements the basic behavior required to produce messages
    for the LOVE manager.

    When subclassing to deal with different kinds of data being, users will
    mostly have to override the `_convert_data_to_dict` private method. This
    method deals with converting especial data types into a dictionary, which
    is then transimitted as a json string by the appropriate methods.

    Parameters
    ----------
    component_name : `str`, optional
        Name of the component for which data will be produced.
    log : `logging.Logger`, optional
        Logger facility.

    Attributes
    ----------
    log : `logging.Logger`
        Logger facility.
    done_task : `asyncio.Future`
        An asyncio future to keep the producer running.
    """

    def __init__(
        self,
        component_name: Optional[str] = None,
        log: Optional[logging.Logger] = None,
        **kwargs,
    ):
        self.log = (
            logging.getLogger(type(self).__name__)
            if log is None
            else log.getChild(type(self).__name__)
        )

        self._component_name: Optional[str] = component_name
        self._component_name_in_manager_message: str = "csc"
        self._love_manager_message: LoveManagerMessage = LoveManagerMessage(
            component_name
        )

        self._send_message: Optional[Callable[[str], None]] = None

        self._period_monitor: float = 2.0

        self._data_to_monitor_periodically_functions: list = []
        self._data_to_monitor_periodically_coroutines: list = []

        self._asynchronous_data_last_samples: dict = dict()
        self._asynchronous_data_category: dict = dict()

        self._additional_data_callbacks: dict = dict()

        self.done_task: asyncio.Future = asyncio.Future()

        self._monitor_periodic_data_task: asyncio.Task = asyncio.create_task(
            self._monitor_periodic_data()
        )

    async def get_initial_state_messages_as_json(self) -> AsyncIterator[int]:
        """Asynchronously generetate all initial state messages.

        Yields
        ------
        initial_state : `str`
            Initial state messages as json.
        """

        yield self.get_message_initial_state_all_as_json()
        yield self.get_message_initial_state_as_json()

    def get_message_initial_state_as_json(self) -> str:
        """Return the initial subscription message for this producer.

        Returns
        -------
        `str`
            Initial state as a json string.

        Raises
        ------
        RuntimeError
            If component_name is not set.
        """
        self.assert_component_name_is_set(
            "Set component name before getting initial state message."
        )

        return self._love_manager_message.get_message_initial_state_as_json()

    def get_message_initial_state_all_as_json(self) -> str:
        """Return the initial subscription message to all producers

        Returns
        -------
        `str`
            Initial state as a json string.
        """
        return self._love_manager_message.get_message_initial_state_all_as_json()

    def get_message_initial_state_as_json_for_csc(self, csc: str) -> str:
        """Return the initial subscription message for a given CSC.

        Returns
        -------
        `str`
            Initial state as a json string.
        """
        return self._love_manager_message.get_message_initial_state_as_json_for_csc(
            csc=csc
        )

    async def reply_to_message_data(self, message_data: dict) -> None:
        """Generate a reply based on the input message_data.

        Parameters
        ----------
        message_data: `dict`
            Input dictionary with information used by the producer to determine
            some action to take.
        """
        if self.should_reply_to_message_data(message_data=message_data):
            self.log.debug(f"Replying to message: {message_data}")
            await self.send_reply_to_message_data(message_data=message_data)
        else:
            self.log.debug(f"No reply needed for: {message_data}")

    def get_data_from_message_data(self, message_data: dict) -> dict:
        return message_data.get("data", [dict()])[0]

    def should_reply_to_message_data(self, message_data: dict) -> bool:
        """Determines whether a reply to message data should be sent.

        Parameters
        ----------
        message_data: `dict`
            Input dictionary with information used by the producer to determine
            some action to take.

        Returns
        -------
        `bool`
            Should reply to message data?
        """
        has_matched_metadata = self.has_matched_metadata(message_data)
        is_data_stream_stored = self.is_data_stream_stored(
            message_data["data"][0]["stream"]
        )
        self.log.debug(
            f"has_matched_metadata={has_matched_metadata}, is_data_stream_stored={is_data_stream_stored}"
        )
        return has_matched_metadata and is_data_stream_stored

    def has_matched_metadata(self, message_data: dict) -> bool:
        """Does the message data has the correct metadata?

        Parameters
        ----------
        message_data: `dict`
            Input dictionary with information used by the producer to determine
            some action to take.

        Returns
        -------
        `bool`
            Does message_data and metadata has matched information?
        """
        metadata = self.get_metadata()
        metadata[self._component_name_in_manager_message] = self.component_name

        data = message_data["data"][0]

        self.log.debug(f"metadata: {metadata}")
        self.log.debug(f"data: {data}")

        return (
            all(
                [
                    data[key] == metadata[key]
                    for key in metadata
                    if (key in data) and (key in metadata)
                ]
            )
            and "stream" in data
        )

    def is_data_stream_stored(self, data_stream: dict) -> bool:
        """Determines if data stream is part of the internal data.

        Parameters
        ----------
        data_stream: `str`
            Name of the data stream.

        Returns
        -------
        `bool`
            Is data stream stored in the asynchonous data samples?
        """
        return all(
            [
                stream in self._asynchronous_data_last_samples
                for stream in data_stream.values()
            ]
        )

    async def send_reply_to_message_data(self, message_data: dict) -> None:
        """Send reply to message data."""
        sample_name = self.get_sample_name(message_data)

        await self.send_message(
            self.get_message_category_as_json(
                category="event", data_as_dict=self.retrieve_one_sample(sample_name)
            )
        )

    async def send_initial_data(self):
        """Send initial data."""

        for sample_name in self._asynchronous_data_last_samples:
            await self.send_message(
                self.get_message_category_as_json(
                    category="event", data_as_dict=self.retrieve_one_sample(sample_name)
                )
            )

    def get_sample_name(self, data_stream: dict) -> str:
        return next(iter(data_stream["data"][0]["stream"].values()))

    def add_metadata(self, **kwargs) -> None:
        self._love_manager_message.add_metadata(**kwargs)

    def get_metadata(self) -> dict:
        return self._love_manager_message.metadata

    def register_monitor_data_periodically(
        self, get_data: Callable[[], Any], category: str
    ) -> None:
        """Register a callable method so it is periodically pooled for data to
        be transimitted.

        Parameters
        ----------
        get_data: `func` or `coroutine`
            Function or coroutine to be called/awaited periodically for data.

        category: `str`
            The data category. Usual options are "telemetry" (default) and
            "event".

        Notes
        -----

        The output of the `get_data` function can be in any format. It will be
        converted to a dictionary by calling `self._convert_data_to_dict` in
        the the data monitor loop (e.g. `self._monitor_periodic_data`). If
        producing especial data types (not `dict`), make sure to subclass
        `self._convert_data_to_dict` appropriately.

        See also
        --------
        _convert_data_to_dict: Convert data type to dictionary.
        _monitor_periodic_data: Method running in the background pooling for
            data.
        """

        self.assert_component_name_is_set("Set component name before registering data.")

        if asyncio.iscoroutinefunction(get_data):
            self.log.debug("Setting awaitable monitor...")
            self._data_to_monitor_periodically_coroutines.append((get_data, category))
        else:
            self.log.debug("Setting function monitor...")
            self._data_to_monitor_periodically_functions.append((get_data, category))

    async def _monitor_periodic_data(self):
        """Internal asynchonous method to periodically pool for data and
        transimit it.
        """

        while not self.done_task.done():
            data_category_to_send_from_functions = [
                (func(), category)
                for func, category in self._data_to_monitor_periodically_functions
            ]

            data_to_send_from_coroutines = await asyncio.gather(
                *[coro() for coro, _ in self._data_to_monitor_periodically_coroutines]
            )
            category_to_send_from_coroutines = [
                category
                for _, category in self._data_to_monitor_periodically_coroutines
            ]

            for data, category in data_category_to_send_from_functions:
                if data is not None:
                    await self.send_message(
                        self.get_message_category_as_json(
                            category=category,
                            data_as_dict=self._convert_data_to_dict(data)[1],
                        )
                    )

            for data, category in zip(
                data_to_send_from_coroutines, category_to_send_from_coroutines
            ):
                await self.send_message(
                    self.get_message_category_as_json(
                        category=category,
                        data_as_dict=self._convert_data_to_dict(data)[1],
                    )
                )

            await asyncio.sleep(self.period_default_in_seconds)

    async def handle_asynchronous_data_callback(self, data: Any) -> None:
        """Callback function to handle asynchonous data.

        Parameters
        ----------
        data:
            Input data.
        """

        data_key, data_as_dict = self._convert_data_to_dict(data)

        self.store_samples(**{data_key: data_as_dict})

        await self.send_message(
            self.get_message_category_as_json(
                category=self.get_asynchronous_data_category(data_key),
                data_as_dict=data_as_dict,
            )
        )

        if data_key in self._additional_data_callbacks:
            await self._additional_data_callbacks[data_key](data)

    def register_asynchronous_data_category(self, name: str, category: str) -> None:
        self._asynchronous_data_category[name] = category

    def get_asynchronous_data_category(self, name) -> str:
        return self._asynchronous_data_category.get(name, "event")

    def store_samples(self, **kwargs: dict) -> None:
        """Store samples in internal asynchronous table.

        Parameters
        ----------
        **kwargs: `dict`
            names, values to store.
        """
        for key in kwargs:
            self._asynchronous_data_last_samples[key] = kwargs[key]

    def retrieve_samples(self, *args: List[str]) -> List[dict]:
        """Return samples from internal asynchronous table.

        Parameters
        ----------
        *args: `list` of `str`
            List of names of samples to retrieve.

        Returns
        -------
        `list` of `dict`
            List of dictionary with the requested samples.
        """

        return [self._asynchronous_data_last_samples[key] for key in args]

    def retrieve_one_sample(self, sample_name: str) -> dict:
        """Retrieve one sample from internal_asynchronous table.

        Parameters
        ----------
        sample_name: `str`
            Name of the sample in internal data structure.

        Returns
        -------
        `dict`
            Sample.
        """
        return self._asynchronous_data_last_samples[sample_name]

    def get_message_category_as_json(self, category: str, data_as_dict: dict) -> str:
        """"""
        return self._love_manager_message.get_message_category_as_json(
            category=category, data=data_as_dict
        )

    def _convert_data_to_dict(self, data: Any) -> Tuple[str, dict]:
        """Convert data to dictionary.

        By default this method only works with dictionaries. To deal with
        especial data types, subclass and override this method.

        Parameters
        ----------
        data:
            Data to convert to dictionary.

        Returns
        -------
        name: `str`
            Assigned name of the kind of data stream.
        data_as_dict: `dict`
            Dictionary with the data payload.

        Raises
        ------
        TypeError:
            If input data is not a dictionary.

        See also
        --------
        handle_asynchronous_data_callback: Coroutine to handle producing
            asynchonous data.
        register_monitor_data_periodically: Register data to be produced
            periodically.
        _monitor_periodic_data: Method running in the background pooling for
            data.
        """

        if not isinstance(data, dict):
            raise TypeError(
                "Default convert data to dict only works with dictionaries. "
                "Subclass and override `_convert_data_to_dict` method to support especial data types."
            )

        data_as_dict = data.copy()

        name = (
            data_as_dict["name"]
            if "name" in data_as_dict
            else self.generate_data_name(repr(data_as_dict.keys()))
        )

        return name, data_as_dict

    def generate_data_name(self, data_repr: str) -> str:
        """Generate data name.

        Parameters
        ----------
        data_repr: `str`
            Data representation, typically repr(data.keys()) for dictionaries.

        Returns
        -------
        `str`
            Hash code for the input data representation.
        """
        return hashlib.sha1(data_repr.encode()).hexdigest()

    def assert_component_name_is_set(self, message: str = "") -> None:
        """Assert that the component name is set.

        Parameters
        ----------
        message: `str`
            Additional message to append to exception message in case of
            assertion error.

        Raises
        ------
        AssertionError:
            If component name is not set.
        """

        assert self._component_name is not None, f"Component name is not set. {message}"

    def register_additional_action(
        self, data_key: str, additional_action: Coroutine
    ) -> None:
        """Register additional actions to take for specific data key.

        Parameters
        ----------
        data_key : `str`
            Data key.
        additional_action : `coroutine`
            Function to call when specified data is received.
        """

        self.log.debug(f"Registering additional action for {data_key}.")
        self._additional_data_callbacks[data_key] = additional_action

    @property
    def period_default_in_seconds(self) -> float:
        return self._period_monitor

    @property
    def send_message(self) -> Callable[[str], None]:
        """Send message function.

        This must be set before the producer can send messages with it. If not
        set and called it will generate a RuntimeError.
        """
        if self._send_message is None:
            raise RuntimeError(
                "Send message not setup. This is needed for the producer to be able "
                "to broadcast messages to clients."
            )

        return self._send_message

    @send_message.setter
    def send_message(self, coro: Optional[Callable[[str], None]]) -> None:
        if coro is not None and not asyncio.iscoroutinefunction(coro):
            raise TypeError(f"coro={coro} not a coroutine function.")

        self._send_message = coro

    @property
    def component_name(self) -> Optional[str]:
        self.assert_component_name_is_set()
        return self._component_name

    @component_name.setter
    def component_name(self, component_name: str) -> None:
        self._component_name = component_name
        self._love_manager_message = LoveManagerMessage(component_name=component_name)

    async def close(self):
        if not self.done_task.done():
            self.done_task.set_result(True)

        try:
            await asyncio.wait_for(
                self._monitor_periodic_data_task, timeout=self._period_monitor * 2
            )
        except asyncio.TimeoutError:
            self._monitor_periodic_data_task.close()
            try:
                await self._monitor_periodic_data_task
            except asyncio.CancelledError:
                pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, type, value, traceback):
        await self.close()
