# -*- coding: utf-8 -*-
# Copyright (c) 2020-2026 Salvador E. Tropea
# Copyright (c) 2020-2026 Instituto Nacional de Tecnología Industrial
# License: GPL-3.0
# Project: KiBot (formerly KiPlot)
from .optionable import Optionable
from .gs import GS
from .misc import W_NOTASCII
from re import match
from .error import (PlotError, KiPlotConfigurationError)
from .macros import macros, document, output_class  # noqa: F401
from . import log

logger = log.get_logger()
assert GS.F_Cu is not None, "layer.py imported before __main__ execution"


LAYER_ORDER = ['F.Cu', 'F.Mask', 'F.SilkS', 'F.Paste', 'F.Adhes', 'F.CrtYd', 'F.Fab', 'Dwgs.User', 'Cmts.User', 'Eco1.User',
               'Eco2.User', 'Edge.Cuts', 'Margin', 'User.1', 'User.2', 'User.3', 'User.4', 'User.5', 'User.6', 'User.7',
               'User.8', 'User.9', 'In1.Cu', 'In2.Cu', 'In3.Cu', 'In4.Cu', 'In5.Cu', 'In6.Cu', 'In7.Cu', 'In8.Cu', 'In9.Cu',
               'In10.Cu', 'In11.Cu', 'In12.Cu', 'In13.Cu', 'In14.Cu', 'In15.Cu', 'In16.Cu', 'In17.Cu', 'In18.Cu', 'In19.Cu',
               'In20.Cu', 'In21.Cu', 'In22.Cu', 'In23.Cu', 'In24.Cu', 'In25.Cu', 'In26.Cu', 'In27.Cu', 'In28.Cu', 'In29.Cu',
               'In30.Cu', 'B.Cu', 'B.Mask', 'B.SilkS', 'B.Paste', 'B.Adhes', 'B.CrtYd', 'B.Fab']
LAYER_PRIORITY = {}


def create_print_priority(board):
    """ Fills LAYER_PRIORITY. This is used to sort layers for printing.
        It is the way KiCad sorts the layers.
        We do it as soon as we have a valid board. """
    global LAYER_PRIORITY
    if len(LAYER_PRIORITY) > 0:
        return
    LAYER_PRIORITY = {board.GetLayerID(name): c for c, name in enumerate(LAYER_ORDER)}


def get_priority(id):
    return LAYER_PRIORITY.get(id, 1e6)


def inner_id_in_range(id, cnt):
    if GS.ki9:
        return GS.layer_is_inner(id) and int(id/2) < cnt
    return id > 0 and id < cnt-1


class Layer(Optionable):
    """ A layer description """
    # Protel extensions
    PROTEL_EXTENSIONS = {
        GS.F_Cu: 'gtl',
        GS.B_Cu: 'gbl',
        GS.F_Adhes: 'gta',
        GS.B_Adhes: 'gba',
        GS.F_Paste: 'gtp',
        GS.B_Paste: 'gbp',
        GS.F_SilkS: 'gto',
        GS.B_SilkS: 'gbo',
        GS.F_Mask: 'gts',
        GS.B_Mask: 'gbs',
        GS.Edge_Cuts: 'gm1',
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
            """ Suffix used in file names related to this layer. Derived from the name if not specified.
                A default can be specified using the `layer_defaults` global option """
            self.description = ''
            """ A description for the layer, for documentation purposes.
                A default can be specified using the `layer_defaults` global option """
        self._unknown_is_error = True
        self._protel_extension = None
        self._layer_example = 'F.Cu'

    def config(self, parent):
        super().config(parent)
        if not self.layer:
            raise KiPlotConfigurationError("Missing or empty `layer` attribute for layer entry ({})".format(self._tree))
        if not self.description:
            self.description = self.get_default_description()
        if not self.suffix:
            self.suffix = self.get_default_suffix()
        self.clean_suffix()

    @staticmethod
    def reset():
        Layer._pcb_layers = None
        Layer._plot_layers = None

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
            self._protel_extension = 'g'+str(GS.inner_layer_index(self.id))
            return
        if self.id in Layer.PROTEL_EXTENSIONS:
            self._protel_extension = Layer.PROTEL_EXTENSIONS[self.id]
            return
        self._protel_extension = 'gbr'
        return

    @classmethod
    def solve(cls, values):
        board = GS.board
        layer_cnt = 2
        if board:
            layer_cnt = board.GetCopperLayerCount()
            create_print_priority(board)
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
                    if layer._is_inner and not inner_id_in_range(layer._id, layer_cnt):
                        raise PlotError("Inner layer `{}` is not valid for this board".format(layer))
                    layer.fix_protel_ext()
                    new_vals.append(layer)
                elif isinstance(layer, int):
                    new_vals.append(cls.create_layer(layer))
                else:  # A string
                    ext = None
                    if layer == 'all':
                        ext = cls._get_layers(Layer._pcb_layers)
                    elif layer == 'selected':
                        ext = cls._get_layers(Layer._plot_layers)
                    elif layer == 'copper':
                        ext = cls._get_layers(Layer._get_copper())
                    elif layer == 'inners':
                        ext = cls._get_layers(Layer._get_inners())
                    elif layer == 'outers':
                        ext = cls._get_layers(Layer._get_outers())
                    elif layer == 'technical':
                        ext = cls._get_layers(Layer._get_technical())
                    elif layer == 'user':
                        ext = cls._get_layers(Layer._get_user())
                    elif layer in Layer._pcb_layers:
                        ext = [cls.create_layer(layer)]
                    # Give compatibility for the KiCad 5 default names (automagically renamed by KiCad 6)
                    elif GS.ki6 and layer in GS.KICAD6_RENAME:
                        ext = [cls.create_layer(GS.KICAD6_RENAME[layer])]
                    elif layer in GS.DEFAULT_LAYER_NAMES:
                        ext = [cls.create_layer(layer)]
                    if ext is None:
                        raise KiPlotConfigurationError("Unknown layer spec: `{}`".format(layer))
                    new_vals.extend(ext)
            return new_vals
        raise AssertionError("Unimplemented layer type "+str(type(values)))

    @staticmethod
    def _get_copper():
        return {GS.board.GetLayerName(id): id for id in GS.board.GetEnabledLayers().CuStack()}

    @staticmethod
    def _get_inners():
        return {GS.board.GetLayerName(id): id for id in GS.board.GetEnabledLayers().CuStack()
                if id != GS.B_Cu and id != GS.F_Cu}

    @staticmethod
    def _get_outers():
        return {GS.board.GetLayerName(id): id for id in GS.board.GetEnabledLayers().CuStack()
                if id == GS.B_Cu or id == GS.F_Cu}

    @staticmethod
    def _get_technical():
        if GS.ki9:
            return {GS.board.GetLayerName(id): id for id in GS.board.GetEnabledLayers().AllTechMask().Seq()}
        return {GS.board.GetLayerName(id): id for id in GS.board.GetEnabledLayers().Technicals()}

    @staticmethod
    def _get_user():
        b = GS.board
        enabled = b.GetEnabledLayers()
        if GS.ki9:
            layers = {b.GetLayerName(id): id for id in enabled.UserMask().Seq()}
            # Applying UserDefinedLayersMask() doesn't work as expected it returns all possible user layers
            # This is why we need the "if id ..." and this why we need to get the list in 2 steps
            layers.update({b.GetLayerName(id): id for id in enabled.UserDefinedLayersMask().Seq() if id in enabled.Seq()})
            return layers
        return {GS.board.GetLayerName(id): id for id in enabled.Users()}

    @staticmethod
    def _set_pcb_layers():
        Layer._pcb_layers = {GS.board.GetLayerName(id): id for id in GS.board.GetEnabledLayers().Seq()}

    def get_default_suffix(self):
        if GS.global_layer_defaults:
            layer = next(filter(lambda x: x.layer == self.layer, GS.global_layer_defaults), None)
            if layer and layer.suffix:
                return layer.suffix
        return self.layer.replace('.', '_')

    def get_default_description(self):
        if GS.global_layer_defaults:
            layer = next(filter(lambda x: x.layer == self.layer, GS.global_layer_defaults), None)
            if layer and layer.description:
                return layer.description
        return GS.DEFAULT_LAYER_DESC.get(self.layer, 'No description')

    @classmethod
    def create_layer(cls, name):
        layer = cls()
        if isinstance(name, str):
            layer.layer = name
            layer._get_layer_id_from_name()
        else:
            layer._id = name
            layer._is_inner = GS.layer_is_inner(name)
            name = GS.board.GetLayerName(name)
            layer.layer = name
        layer.suffix = layer.get_default_suffix()
        layer.description = layer.get_default_description()
        layer.fix_protel_ext()
        layer.clean_suffix()
        return layer

    @classmethod
    def _get_layers(cls, d_layers):
        layers = []
        for n in d_layers.keys():
            layers.append(cls.create_layer(n))
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
        if self.layer in GS.DEFAULT_LAYER_NAMES:
            self._id = GS.DEFAULT_LAYER_NAMES[self.layer]
            self._is_inner = self.layer in GS.DEFAULT_INNER_LAYER_NAMES
        else:
            id = Layer._pcb_layers.get(self.layer)
            if id is not None:
                # 2) List from the PCB
                self._id = id
                self._is_inner = GS.layer_is_inner(id)
            elif self.layer.startswith("Inner"):
                # 3) Inner.N names
                m = match(r"^Inner\.([0-9]+)$", self.layer)
                if not m:
                    raise KiPlotConfigurationError("Malformed inner layer name: `{}`, use Inner.N".format(self.layer))
                id = int(m.group(1))
                self._id = (id+1)*2 if GS.ki9 else id
                self._is_inner = True
            else:
                raise KiPlotConfigurationError("Unknown layer name: `{}`".format(self.layer))
        return self._id

    def is_copper(self):
        if GS.pn is not None:
            return self._id >= GS.F_Cu and self._id <= GS.B_Cu
        return GS.kp.util.board_layer.is_copper_layer(self._id)

    def is_top(self):
        return self._id == GS.F_Cu

    def is_bottom(self):
        return self._id == GS.B_Cu

    def __str__(self):
        if hasattr(self, '_id'):
            return "{} ({} '{}' {})".format(self.layer, self._id, self.description, self.suffix)
        return "{} ('{}' {})".format(self.layer, self.description, self.suffix)

    @staticmethod
    def id2def_name(id):
        if GS.ki5:
            return GS.ID_2_DEFAULT_NAME[id]
        return GS.pn.LayerName(id) if GS.pn is not None else GS.kp.canonical_name(id)
