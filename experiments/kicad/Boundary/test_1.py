import sys
import pcbnew
ToMM = pcbnew.ToMM

def get_shape_bbox(s, exact):
    """ Bounding box without the width of the trace """
    if not exact:
        return s.GetBoundingBox()
    width = s.GetWidth()
    s.SetWidth(0)
    bbox = s.GetBoundingBox()
    s.SetWidth(width)
    return bbox


def boundary_box_to_corners(bb):
    if bb is None:
        return (0, 0, 0, 0)
    start = bb.GetOrigin()
    end = bb.GetEnd()
    return (start.x, start.y, end.x, end.y)


def merge_boundary_boxes(current, added):
    if current is None:
        return added
    current.Merge(added)
    return current


def compute_boundary_k5(board, layers, classes, exact=True):
    res = None
    for d in board.GetDrawings():
        if d.GetClass() in classes and d.GetLayer() in layers:
            res = merge_boundary_boxes(res, get_shape_bbox(d, exact))
    # Now inside footprints
    for m in board.GetFootprints():
        for gi in m.GraphicalItems():
            if gi.GetClass() in classes and gi.GetLayer() in layers:
                res = merge_boundary_boxes(res, get_shape_bbox(gi, exact))
    return boundary_box_to_corners(res)


def compute_pcb_boundary_k5(board):
    return compute_boundary_k5(board, set([board.GetLayerID('Edge.Cuts')]), set(['PCB_SHAPE']))


def print_rect(bb):
    print(f"({ToMM(bb.GetX())},{ToMM(bb.GetY())}) {ToMM(bb.GetWidth())} x {ToMM(bb.GetHeight())}")

board = pcbnew.LoadBoard(sys.argv[1])

# PCB edge, including the width of the lines. Only shapes.
print("ComputeBoundingBox, edge only True")
print_rect(board.ComputeBoundingBox(aBoardEdgesOnly=True))

# Everything, including the width of the lines. Text is included. Drawing and comments also included
print("ComputeBoundingBox, edge only False")
print_rect(board.ComputeBoundingBox(aBoardEdgesOnly=False))

# PCB edge, excluding the width of the lines. Only shapes.
print("compute_pcb_boundary_k5, edge only")
bb = compute_pcb_boundary_k5(board)
print(f"({ToMM(bb[0])},{ToMM(bb[1])}) {ToMM(bb[2]-bb[0])} x {ToMM(bb[3]-bb[1])}")

# Exclude drawings, include text, include trace width
layer_names = ('Edge.Cuts', 'F.Mask', 'F.Cu', 'F.SilkS')
layers = set(board.GetLayerID(la) for la in layer_names)
bb = compute_boundary_k5(board, layers, set(['PCB_SHAPE', 'PTEXT', 'PCB_TEXT']), exact=False)
print("compute_pcb_boundary_k5, PcbDraw layers, top")
print(f"({ToMM(bb[0])},{ToMM(bb[1])}) {ToMM(bb[2]-bb[0])} x {ToMM(bb[3]-bb[1])}")


"""
tests/board_samples/kicad_*/boundary_box_test.kicad_pcb

KiCad 6
ComputeBoundingBox, edge only True
(94.975,94.975) 11.05 x 11.05
ComputeBoundingBox, edge only False
(89.95,86.5675) 27.092857 x 27.865
compute_pcb_boundary_k5, edge only
(95.0,95.0) 11.0 x 11.0
compute_pcb_boundary_k5, PcbDraw layers, top
(94.975,86.5675) 22.067857 x 19.4575

KiCad 7/8/9/10
ComputeBoundingBox, edge only True
(94.975,94.975) 11.05 x 11.05
ComputeBoundingBox, edge only False
(89.95,86.596) 27.242857 x 27.808
compute_pcb_boundary_k5, edge only
(95.0,95.0) 11.0 x 11.0
compute_pcb_boundary_k5, PcbDraw layers, top
(94.975,86.596) 22.217857 x 19.429
"""
