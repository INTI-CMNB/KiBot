# Author: Salvador E. Tropea
# License: MIT
# numpy replacement for PcbDraw
import builtins
from operator import itemgetter

# A value that is not None
float32 = 1

def argmin(vector):
    """ Index of the minimum element in a vector.
        See https://stackoverflow.com/questions/13300962/python-find-index-of-minimum-item-in-list-of-floats """
    return min(enumerate(vector), key=itemgetter(1))[0]


def array(data, dtype=None):
    """ Just make all elements float, or let unchanged """
    if dtype:
        for r in data:
            for c, val in enumerate(r):
                r[c] = float(val)
    return data


def matmul(A, B):
    """ Matrix multiplication.
        See: https://geekflare.com/multiply-matrices-in-python/ """
    # Ensure the number of cols in A is the same as the number of rows in B
    # assert len(A[0]) == len(B)
    return [[sum(a*b for a, b in zip(A_row, B_col)) for B_col in zip(*B)] for A_row in A]


def ones(count, dtype=None):
    assert dtype == bool
    return [True] * count


def empty(sizes):
    return []


def any(data):
    return builtins.any(data)


def argmax(data):
    try:
        i = data.index(True)
    except ValueError:
        i = 0
    return i
