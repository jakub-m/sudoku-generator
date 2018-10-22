#!/usr/bin/env python3.6

'''Generator of sudoku boards of different size and difficulty.'''

import collections
import itertools
import sys

EMPTY_FIELD = '.'

# Template of the board. "." stands for empty field
BOARD_TEMPLATE='''
111222333
111222333
111222333
444555666
444555666
444555666
777888999
777888999
777888999
'''


class Board:
    '''A Board contains information about size of the board, information about
    Sections and occupancies of the Fields. A Field is the smallest element of
    the Board. A Section is a collection of indexes of the Fields on the Board.
    To make a Board valid, all the Sections of the board are heterogenous. A
    Section is heterogenous if all the Fields of that Section are different, or
    empty. A Section is full if all the Fields of that Section are non-empty.
    '''

    def __init__(self):
        pass


class Segment:
    def __init__(self, coords):
        '''coords is a list of coordinates: [(i_row, i_col), ...]'''
        coords = list(coords)
        self._validate(coords)
        self.coords = coords

    def __str__(self):
        return 'S{}'.format(self.coords)

    def _validate(self, coords):
        '''Validate that there are no duplicates in the input parameters.'''
        seen = set()
        for cc in coords:
            if cc in seen:
                raise ValueError('Value {} appears twice in: {}'.format(cc, coords))
            seen.add(cc)


def board_from_template(template):
    height, width, grid = template_to_grid(template)
    segments_rows = list(iter_segments_for_rows(height, width, grid))
    segments_cols = list(iter_segments_for_cols(height, width, grid))
    validate_two_segments(segments_rows, segments_cols)
    segments_symbols = list(iter_segments_for_symbols(height, width, grid))
    validate_two_segments(segments_symbols, segments_rows)
    validate_two_segments(segments_symbols, segments_cols)


def template_to_grid(template):
    '''Return height, width, grid. Height stands for the range of the first
    parameter of the grid (row). Weight is range of the second parameter of the
    grid (col).'''
    lines = [s.strip() for s in template.split()]
    lines = [s for s in lines if s]
    height = len(lines)
    widths = set(len(s) for s in lines)
    if len(widths) != 1:
        raise ValueError('Rows have different lenghts. Lengths: {}'.format(widths))
    width = sorted(widths)[0]
    grid = {}
    for i_row, line in enumerate(lines):
        for i_col, c in enumerate(line):
            coord = (i_row, i_col)
            grid[coord] = c
    return height, width, grid


def validate_two_segments(segments_a, segments_b):
    '''Validation. Segments for rows and cols should cover same fields.'''
    set_coords_a = flatten_and_validate_segments(segments_a)
    set_coords_b = flatten_and_validate_segments(segments_b)
    union = set_coords_a | set_coords_b
    odds = (union - set_coords_a) | (union - set_coords_b)
    if odds:
        raise ValueError('There are coordinates not shared by two lists of segments: {}'.format(odds))


def flatten_and_validate_segments(segments):
    '''Return set of coordinates from all the segments.'''
    set_coords = set()
    for seg in segments:
        cc = set(seg.coords)
        intersection = cc.intersection(set_coords)
        if intersection:
            raise ValueError('There is an intersection {} in segments:\n\t{}'.format(intersection, '\n\t'.join(str(s) for s in segments)))
        set_coords |= cc
    return set_coords


def iter_segments_for_rows(height, width, grid):
    for i_row in range(height):
        line = [grid[(i_row, i_col)] for i_col in range(width)]
        disjoint_indices = list(iter_disjoint_indices(line))
        for indices in disjoint_indices:
            yield Segment([(i_row, i) for i in indices])


def iter_segments_for_cols(height, width, grid):
    for i_col in range(width):
        line = [grid[(i_row, i_col)] for i_row in range(height)]
        disjoint_indices = list(iter_disjoint_indices(line))
        for indices in disjoint_indices:
            yield Segment([(i, i_col) for i in indices])


def iter_segments_for_symbols(height, width, grid):
    '''Iterate segments based on actual symbol.'''
    segments_by_symbol = collections.defaultdict(list)
    for (i_row, i_col) in itertools.product(range(height), range(width)):
        coord = (i_row, i_col)
        symbol = grid[coord]
        if symbol is EMPTY_FIELD:
            continue
        segments_by_symbol[symbol].append(coord)
    for s in segments_by_symbol:
        yield Segment(segments_by_symbol[s])


def iter_disjoint_indices(line):
    '''EMPTY_FIELD in line means a break between indices. A break should result
    in a separate Segment.'''
    indices = set()
    for i, c in enumerate(line):
        if c is EMPTY_FIELD:
            if indices:
                yield indices
                indices = set()
        else:
            indices.add(i)
    if indices:
        yield indices


def log(message):
    print(message, file=sys.stderr)


def main():
    template = board_from_template(BOARD_TEMPLATE)
    print(template)


if __name__=="__main__":
    main()
