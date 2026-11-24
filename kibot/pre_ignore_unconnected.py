# -*- coding: utf-8 -*-
# Copyright (c) 2020-2024 Salvador E. Tropea
# Copyright (c) 2020-2024 Instituto Nacional de Tecnología Industrial
# License: AGPL-3.0
# Project: KiBot (formerly KiPlot)
from .misc import W_DEPR
from .macros import macros, document, pre_class  # noqa: F401
from .log import get_logger
logger = get_logger(__name__)


@pre_class
class Ignore_Unconnected(BasePreFlight):  # noqa: F821
    """ Ignore Unconnected (**Deprecated**)
        Option for `run_drc`. Ignores the unconnected nets. Useful if you didn't finish the routing.
        It will also ignore KiCad 6 warnings when using `run_drc`.
        Use the `ignore_unconnected` option from `run_drc`/`drc` instead """
    def __init__(self):
        super().__init__()
        with document:
            self.ignore_unconnected = False
            """ Enable this preflight """

    def config(self, parent):
        super().config(parent)
        logger.warning(W_DEPR+'The `ignore_unconnected` preflight is deprecated, use the `ignore_unconnected` option')

    def get_example() -> str:
        """ Returns a YAML value for the example config """
        return 'false'

    def apply(self):
        BasePreFlight._set_option('ignore_unconnected', self._enabled)  # noqa: F821
