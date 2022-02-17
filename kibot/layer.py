# -*- coding: utf-8 -*-
# Copyright (c) 2020-2021 Salvador E. Tropea
# Copyright (c) 2020-2021 Instituto Nacional de Tecnología Industrial
# License: GPL-3.0
# Project: KiBot (formerly KiPlot)
import pcbnew
from .optionable import Optionable
from .gs import GS
from .misc import W_NOTASCII
from re import match
from .error import (PlotError, KiPlotConfigurationError)
from .macros import macros, document, output_class  # noqa: F401
from . import log

logger = log.get_logger()


class Layer(Optionable):
    """ A layer description """
    # Default names
    DEFAULT_LAYER_NAMES = {
        'F.Cu': pcbnew.F_Cu,
        'B.Cu': pcbnew.B_Cu,
        'F.Adhes': pcbnew.F_Adhes,
        'B.Adhes': pcbnew.B_Adhes,
        'F.Paste': pcbnew.F_Paste,
        'B.Paste': pcbnew.B_Paste,
        'F.SilkS': pcbnew.F_SilkS,
        'B.SilkS': pcbnew.B_SilkS,
        'F.Mask': pcbnew.F_Mask,
        'B.Mask': pcbnew.B_Mask,
        'Dwgs.User': pcbnew.Dwgs_User,
        'Cmts.User': pcbnew.Cmts_User,
        'Eco1.User': pcbnew.Eco1_User,
        'Eco2.User': pcbnew.Eco2_User,
        'Edge.Cuts': pcbnew.Edge_Cuts,
        'Margin': pcbnew.Margin,
        'F.CrtYd': pcbnew.F_CrtYd,
        'B.CrtYd': pcbnew.B_CrtYd,
        'F.Fab': pcbnew.F_Fab,
        'B.Fab': pcbnew.B_Fab,
    }
    # Default names
    DEFAULT_LAYER_DESC = {
        'F.Cu': 'Front copper',
        'B.Cu': 'Bottom copper',
        'F.Adhes': 'Front adhesive (glue)',
        'B.Adhes': 'Bottom adhesive (glue)',
        'F.Paste': 'Front solder paste',
        'B.Paste': 'Bottom solder paste',
        'F.SilkS': 'Front silkscreen (artwork)',
        'B.SilkS': 'Bottom silkscreen (artwork)',
        'F.Mask': 'Front soldermask (negative)',
        'B.Mask': 'Bottom soldermask (negative)',
        'Dwgs.User': 'User drawings',
        'Cmts.User': 'User comments',
        'Eco1.User': 'For user usage 1',
        'Eco2.User': 'For user usage 2',
        'Edge.Cuts': 'Board shape',
        'Margin': 'Margin relative to edge cut',
        'F.CrtYd': 'Front courtyard area',
        'B.CrtYd': 'Bottom courtyard area',
        'F.Fab': 'Front documentation',
        'B.Fab': 'Bottom documentation',
    }
    KICAD6_RENAME = {
        'F.Adhes': 'F.Adhesive',
        'B.Adhes': 'B.Adhesive',
        'F.SilkS': 'F.Silkscreen',
        'B.SilkS': 'B.Silkscreen',
        'Dwgs.User': 'User.Drawings',
        'Cmts.User': 'User.Comments',
        'Eco1.User': 'User.Eco1',
        'Eco2.User': 'User.Eco2',
        'F.CrtYd': 'F.Courtyard',
        'B.CrtYd': 'B.Courtyard',
    }
    # Protel extensions
    PROTEL_EXTENSIONS = {
        pcbnew.F_Cu: 'gtl',
        pcbnew.B_Cu: 'gbl',
        pcbnew.F_Adhes: 'gta',
        pcbnew.B_Adhes: 'gba',
        pcbnew.F_Paste: 'gtp',
        pcbnew.B_Paste: 'gbp',
        pcbnew.F_SilkS: 'gto',
        pcbnew.B_SilkS: 'gbo',
        pcbnew.F_Mask: 'gts',
        pcbnew.B_Mask: 'gbs',
        pcbnew.Edge_Cuts: 'gm1',
    }
    # Names from the board file
    _pcb_layers = None
    _plot_layers = None

    def __init__(self):
        super().__init__()
        with document:
            self.layer = ''
            """ Name of the layer. As you see it in KiCad """
            self.suffix = ''
            """ Suffix used in file names related to this layer. Derived from the name if not specified """
            self.description = ''
            """ A description for the layer, for documentation purposes """
        self._unknown_is_error = True
        self._protel_extension = None

    def config(self, parent):
        super().config(parent)
        if not self.layer:
            raise KiPlotConfigurationError("Missing or empty `layer` attribute for layer entry ({})".format(self._tree))
        if not self.description:
            if self.layer in Layer.DEFAULT_LAYER_DESC:
                self.description = Layer.DEFAULT_LAYER_DESC[self.layer]
            else:
                self.description = 'No description'
        if not self.suffix:
            self.suffix = self.layer.replace('.', '_')
        self.clean_suffix()

    def clean_suffix(self):
        filtered_suffix = ''.join(char for char in self.suffix if ord(char) < 128)
        if filtered_suffix != self.suffix:
            logger.warning(W_NOTASCII+'Only ASCII chars are allowed for layer suffixes ({}), using {}'.
                           format(self, filtered_suffix))
            self.suffix = filtered_suffix

    @property
    def id(self):
        return self._id

    def fix_protel_ext(self):
        """ Makes sure we have a defined Protel extension """
        if self._protel_extension is not None:
            # Already set, keep it
            return
        if self._is_inner:
            self._protel_extension = 'g'+str(self.id-pcbnew.F_Cu+1)
            return
        if self.id in Layer.PROTEL_EXTENSIONS:
            self._protel_extension = Layer.PROTEL_EXTENSIONS[self.id]
            return
        self._protel_extension = 'gbr'
        return

    @staticmethod
    def solve(values):
        board = GS.board
        layer_cnt = 2
        if board:
            layer_cnt = board.GetCopperLayerCount()
        # Get the list of used layers from the board
        # Used for 'all' but also to validate the layer names
        if Layer._pcb_layers is None:
            Layer._pcb_layers = {}
            if board:
                Layer._set_pcb_layers()
        # Get the list of selected layers for plot operations from the board
        if Layer._plot_layers is None:
            Layer._plot_layers = {}
            if board:
                Layer._set_plot_layers()
        # Solve string
        if isinstance(values, str):
            values = [values]
        # Solve list
        if isinstance(values, list):
            new_vals = []
            for layer in values:
                if isinstance(layer, Layer):
                    layer._get_layer_id_from_name()
                    # Check if the layer is in use
                    if layer._is_inner and (layer._id < 1 or layer._id >= layer_cnt - 1):
                        raise PlotError("Inner layer `{}` is not valid for this board".format(layer))
                    layer.fix_protel_ext()
                    new_vals.append(layer)
                else:  # A string
                    ext = None
                    if layer == 'all':
                        ext = Layer._get_layers(Layer._pcb_layers)
                    elif layer == 'selected':
                        ext = Layer._get_layers(Layer._plot_layers)
                    elif layer == 'copper':
                        ext = Layer._get_layers(Layer._get_copper())
                    elif layer == 'technical':
                        ext = Layer._get_layers(Layer._get_technical())
                    elif layer == 'user':
                        ext = Layer._get_layers(Layer._get_user())
                    elif layer in Layer._pcb_layers:
                        ext = [Layer.create_layer(layer)]
                    # Give compatibility for the KiCad 5 default names (automagically renamed by KiCad 6)
                    elif GS.ki6() and layer in Layer.KICAD6_RENAME:
                        ext = [Layer.create_layer(Layer.KICAD6_RENAME[layer])]
                    elif layer in Layer.DEFAULT_LAYER_NAMES:
                        ext = [Layer.create_layer(layer)]
                    if ext is None:
                        raise KiPlotConfigurationError("Unknown layer spec: `{}`".format(layer))
                    new_vals.extend(ext)
            return new_vals
        assert False, "Unimplemented layer type "+str(type(values))

    @staticmethod
    def _get_copper():
        return {GS.board.GetLayerName(id): id for id in GS.board.GetEnabledLayers().CuStack()}

    @staticmethod
    def _get_technical():
        return {GS.board.GetLayerName(id): id for id in GS.board.GetEnabledLayers().Technicals()}

    @staticmethod
    def _get_user():
        return {GS.board.GetLayerName(id): id for id in GS.board.GetEnabledLayers().Users()}

    @staticmethod
    def _set_pcb_layers():
        Layer._pcb_layers = {GS.board.GetLayerName(id): id for id in GS.board.GetEnabledLayers().Seq()}

    @classmethod
    def create_layer(cls, name):
        layer = cls()
        layer.layer = name
        layer.suffix = name.replace('.', '_')
        layer.description = Layer.DEFAULT_LAYER_DESC.get(name)
        layer._get_layer_id_from_name()
        layer.fix_protel_ext()
        layer.clean_suffix()
        return layer

    @staticmethod
    def _get_layers(d_layers):
        layers = []
        for n, id in d_layers.items():
            layers.append(Layer.create_layer(n))
        return layers

    @staticmethod
    def _set_plot_layers():
        board = GS.board
        enabled = board.GetEnabledLayers().Seq()
        for id in board.GetPlotOptions().GetLayerSelection().Seq():
            if id in enabled:
                Layer._plot_layers[board.GetLayerName(id)] = id

    def _get_layer_id_from_name(self):
        """ Get the pcbnew layer from the string provided in the config """
        # Priority
        # 1) Internal list
        if self.layer in Layer.DEFAULT_LAYER_NAMES:
            self._id = Layer.DEFAULT_LAYER_NAMES[self.layer]
            self._is_inner = False
        else:
            id = Layer._pcb_layers.get(self.layer)
            if id is not None:
                # 2) List from the PCB
                self._id = id
                self._is_inner = id > pcbnew.F_Cu and id < pcbnew.B_Cu
            elif self.layer.startswith("Inner"):
                # 3) Inner.N names
                m = match(r"^Inner\.([0-9]+)$", self.layer)
                if not m:
                    raise KiPlotConfigurationError("Malformed inner layer name: `{}`, use Inner.N".format(self.layer))
                self._id = int(m.group(1))
                self._is_inner = True
            else:
                raise KiPlotConfigurationError("Unknown layer name: `{}`".format(self.layer))
        return self._id

    def __str__(self):
        if hasattr(self, '_id'):
            return "{} ({} '{}' {})".format(self.layer, self._id, self.description, self.suffix)
        return "{} ('{}' {})".format(self.layer, self.description, self.suffix)


for i in range(1, 30):
    name = 'In'+str(i)+'.Cu'
    Layer.DEFAULT_LAYER_NAMES[name] = pcbnew.In1_Cu+i-1
    Layer.DEFAULT_LAYER_DESC[name] = 'Inner layer '+str(i)
