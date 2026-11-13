# -*- coding: utf-8 -*-
# Copyright (c) 2024 Salvador E. Tropea
# Copyright (c) 2024 Instituto Nacional de Tecnología Industrial
# License: AGPL-3.0
# Project: KiBot (formerly KiPlot)
import os
from shutil import rmtree
from .error import KiPlotConfigurationError
from .gs import GS
from .kicad.pcb import save_pcb_from_sexp
from .kicad.sexpdata import Symbol
from .kicad.sexp_helpers import load_sexp_file
from .kiplot import load_board
from .misc import pretty_list, W_NOPCBTB
from .optionable import Optionable
from .macros import macros, document, pre_class  # noqa: F401
from . import log

logger = log.get_logger()
NOT_MERGABLE = {'version', 'generator', 'generator_version', 'general', 'paper', 'title_block', 'layers', 'setup'}


class PCB_Reference(Optionable):
    """  """
    def __init__(self):
        super().__init__()
        self._unknown_is_error = True
        with document:
            self.name = ''
            """ Text used in the textbox """
            self.file = ''
            """ PCB to insert at the textbox """
        self._name_example = 'First'
        self._file_example = 'first_pcb.kicad_pcb'

    def __str__(self):
        return f'{self.name} -> {self.file}'

    def config(self, parent):
        super().config(parent)
        if not self.name:
            raise KiPlotConfigurationError("Missing PCB name ({})".format(str(self._tree)))
        if not self.file:
            raise KiPlotConfigurationError("Missing PCB file name ({})".format(str(self._tree)))


def merge_pcbs(base, added):
    base = base[0]
    added = added[0]
    # Note: Let the "net" items, we will load the resulting PCB and make KiCad save it. In the process nets are
    # merged
    for e in added:
        if isinstance(e, Symbol):
            pass
        elif isinstance(e, list):
            kind = e[0].value()
            if kind not in NOT_MERGABLE:
                base.append(e)
        else:
            raise KiPlotConfigurationError(f"Malformed PCB ({e})")


@pre_class
class Consolidate_PCBs(BasePreFlight):  # noqa: F821
    """ Consolidate PCBs
        Paste one or more PCBs into an existing PCB.
        This is experimental and isn't intended for generating a PCB to work, just for 3D modeling and/or printing.
        In the main PCB you just draw text boxes containing a name. Here you map this name to a PCB file name.
        After executing this preflight the current PCB contains the references PCBs at the text boxes coordinates.
        Only the top left corner of the text box is relevant.
        An example can be found [here](https://github.com/INTI-CMNB/KiBot/tree/dev/docs/samples/Consolidate_PCBs)
        """
    def __init__(self):
        super().__init__()
        self._pcb_related = True
        with document:
            self.consolidate_pcbs = PCB_Reference
            """ [dict|list(dict)=[]] One or more PCBs to include """

    def __str__(self):
        return f'{pretty_list([v.name for v in self.consolidate_pcbs])}'

    def get_example():
        """ Returns a YAML value for the example config """
        return "\n    - name: 'A name for the PCB'\n      file: 'PATH/TO/PCB/FILE'"

    def apply(self):
        o = self.consolidate_pcbs
        if len(o) == 0:
            return
        if GS.ki5:
            raise KiPlotConfigurationError("The `Consolidate_PCBs` preflight is for KiCad 6 or newer")
        # Create a simple dict
        boards = {p.name.lower(): p.file for p in o}
        # Look for the text boxes
        load_board()
        boxes = {}
        to_remove = []
        for g in GS.board.GetDrawings():
            if g.GetClass() == 'PCB_TEXTBOX':
                name = g.GetText().strip().lower()
                if name in boards:
                    boxes[name] = g.GetPosition()  # (g.GetX(), g.GetY())
                    to_remove.append(g)
        logger.debug('Text boxes we found: '+str(boxes))
        # If no boxes assume we don't need to change anything
        if not len(boxes):
            logger.warning(W_NOPCBTB+"No text boxes to replace, assuming we already replaced them")
            return
        # Check we got all the coordinates
        if len(boxes) != len(boards):
            raise KiPlotConfigurationError(f"Missing text boxes for {list(boards.keys()-boxes.keys())}")
        # Remove the boxes
        for b in to_remove:
            GS.board.Delete(b)
        tmp_dir = GS.mkdtemp('consolidate_pcb')
        # Save to a temporal
        tmp_base = os.path.join(tmp_dir, GS.pcb_fname)
        GS.save_pcb(tmp_base, GS.board)
        # Create intermediate files with the board moved
        tmp_files = []
        for b, f in boards.items():
            board = load_board(f, forced=True)
            bbox = board.GetBoundingBox()
            logger.debug(f'- Processing {b}')
            logger.debug(f"  - Current origin {tuple(map(GS.to_mm, bbox.GetOrigin()))}")
            logger.debug(f"  - New origin {tuple(map(GS.to_mm, boxes[b]))}")
            move_vector = boxes[b]-bbox.GetOrigin()
            logger.debug(f"  - Move vector {tuple(map(GS.to_mm, move_vector))}")
            GS.move_board_items(move_vector)
            tmp_name = os.path.join(tmp_dir, GS.sanitize_file_name(b)+'.kicad_pcb')
            GS.save_pcb(tmp_name, GS.board)
            tmp_files.append(tmp_name)
        # Consolidate the files
        pcb_sexp = load_sexp_file(tmp_base)
        for pcb in tmp_files:
            new_pcb_sexp = load_sexp_file(pcb)
            merge_pcbs(pcb_sexp, new_pcb_sexp)
        save_pcb_from_sexp(pcb_sexp, logger)
        rmtree(tmp_dir)
