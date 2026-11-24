# -*- coding: utf-8 -*-
# Copyright (c) 2021-2024 Salvador E. Tropea
# Copyright (c) 2021-2024 Instituto Nacional de Tecnología Industrial
# License: AGPL-3.0
# Project: KiBot (formerly KiPlot)
from .misc import W_DEPR
from .macros import macros, document, pre_class  # noqa: F401
from .log import get_logger
logger = get_logger(__name__)


@pre_class
class ERC_Warnings(BasePreFlight):  # noqa: F821
    """ ERC Warnings (**Deprecated**)
        Option for `run_erc`. ERC warnings are considered errors.
        Use the `warnings_as_errors` option from `run_erc`/`erc` instead """
    def __init__(self):
        super().__init__()
        with document:
            self.erc_warnings = False
            """ Enable this preflight """

    def config(self, parent):
        super().config(parent)
        logger.warning(W_DEPR+'The `erc_warnings` preflight is deprecated, use the `warnings_as_errors` option')

    def get_example() -> str:
        """ Returns a YAML value for the example config """
        return 'false'

    def apply(self):
        BasePreFlight._set_option('erc_warnings', self._enabled)  # noqa: F821
