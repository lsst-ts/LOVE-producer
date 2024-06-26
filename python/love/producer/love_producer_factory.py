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

__all__ = ["LoveProducerFactory"]

from love.producer.love_producer_base import LoveProducerBase
from love.producer.love_producer_csc import LoveProducerCSC
from love.producer.love_producer_script_queue import LoveProducerScriptQueue
from love.producer.love_producer_watcher import LoveProducerWatcher
from love.producer.producer_utils import get_available_components
from lsst.ts import salobj


class LoveProducerFactory:
    available_love_producer_type = dict(
        base=LoveProducerBase,
        csc=LoveProducerCSC,
        scriptqueue=LoveProducerScriptQueue,
        watcher=LoveProducerWatcher,
    )

    named_love_producer_type = dict(
        ScriptQueue="scriptqueue",
        Watcher="watcher",
    )

    @classmethod
    def get_love_producer_from_type(
        cls, love_producer_type: str, **kwargs
    ) -> LoveProducerBase:
        if love_producer_type in cls.available_love_producer_type:
            return cls.available_love_producer_type[love_producer_type](**kwargs)
        else:
            raise RuntimeError(
                f"Unrecognized love producer type {love_producer_type}. "
                f"Must be one of {cls.available_love_producer_type.keys()}"
            )

    @classmethod
    def get_love_producer_from_name(
        cls, component_name: str, **kwargs
    ) -> LoveProducerBase:
        csc_names = get_available_components()

        name, index = salobj.name_to_name_index(component_name)

        love_producer_from_type_kwargs = kwargs.copy()

        for key in {"csc", "salindex"}:
            if key in love_producer_from_type_kwargs:
                love_producer_from_type_kwargs.pop(key)

        love_producer = cls.get_love_producer_from_type(
            love_producer_type=cls.named_love_producer_type.get(
                name, "csc" if name in csc_names else "base"
            ),
            csc=name,
            salindex=index,
            **love_producer_from_type_kwargs,
        )
        love_producer.component_name = name
        return love_producer
