#!/usr/bin/env python3.6

'''Generator of sudoku boards of different size and difficulty.'''

import collections
import itertools
import sys

# Empty field is a placeholder in the template that is not a part of the Board.
EMPTY_FIELD = ' '

# Unknown value in a field.
UNKNOWN_FIELD = '?'

# Template of the board. "." stands for empty field
BOARD_TEMPLATE='''
aaaBBBccc
aaaBBBccc
aaaBBBccc
DDDeeeFFF
DDDeeeFFF
DDDeeeFFF
gggHHHiii
gggHHHiii
gggHHHiii
'''

# Symbols allowed on the board. They do not need to match the symbols in the
# board template.
BOARD_SYMBOLS = '123456789'


class Board:
    '''A Board contains information about size of the board, information about
    Sections and occupancies of the Fields. A Field is the smallest element of
    the Board. A Section is a collection of indexes of the Fields on the Board.
    To make a Board valid, all the Sections of the board are heterogenous. A
    Section is heterogenous if all the Fields of that Section are different, or
    empty. A Section is full if all the Fields of that Section are non-empty.
    '''

    def __init__(self, height, width, segments, symbols):
        '''segments are all the Segments composing the Board. The Board does
        not have notion of rows, colums or any kind of areas, only Segments.'''
        self.height, self.width = height, width
        self.segments = segments
        self.symbols = symbols
        # All the coordinates from all the segments.
        self._all_coords = self._get_all_coords(segments)
        # Map of coordinates with values. Coordinates not in the map have
        # default value of UNKNOWN_FIELD. NOTE: this can be OPTIMIZED
        # memorywise, since the next board will copy this field.
        self._filled = {}

    def _get_all_coords(self, segments):
        '''Return coordinates of all the fields form all the segments.'''
        return sorted(set(coord for seg in segments for coord in seg.coords))

    def __str__(self):
        lines = [[EMPTY_FIELD] * self.width for _ in range(self.height)]
        for (i_row, i_col) in self._all_coords:
            symbol = self._filled.get((i_row, i_col), UNKNOWN_FIELD)
            lines[i_row][i_col] = symbol
        return '\n'.join(''.join(line) for line in lines)


class Segment:
    def __init__(self, coords):
        '''coords is a list of coordinates: [(i_row, i_col), ...]'''
        coords = list(coords)
        self._validate(coords)
        self.coords = coords

    def __str__(self):
        return 'S{}'.format(self.coords)

    def __len__(self):
        return len(self.coords)

    def _validate(self, coords):
        '''Validate that there are no duplicates in the input parameters.'''
        seen = set()
        for cc in coords:
            if cc in seen:
                raise ValueError('Value {} appears twice in: {}'.format(cc, coords))
            seen.add(cc)


def board_from_template(template, symbols):
    height, width, grid = template_to_grid(template)
    segments_rows = list(iter_segments_for_rows(height, width, grid))
    segments_cols = list(iter_segments_for_cols(height, width, grid))
    validate_two_segments(segments_rows, segments_cols)
    segments_symbols = list(iter_segments_for_symbols(height, width, grid))
    validate_two_segments(segments_symbols, segments_rows)
    validate_two_segments(segments_symbols, segments_cols)
    all_segments = [seg for segments in [segments_rows, segments_cols, segments_symbols] for seg in segments ]
    validate_segments_length(all_segments, symbols)
    return Board(height, width, all_segments, symbols)


def template_to_grid(template):
    '''Return height, width, grid. Height stands for the range of the first
    parameter of the grid (row). Weight is range of the second parameter of the
    grid (col).'''
    lines = [s.strip() for s in template.split('\n')]
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


def validate_segments_length(segments, symbols):
    '''Validate that no segment is longer than the number of the symbols.'''
    for seg in segments:
        if len(seg) > len(symbols):
            raise ValueError('Segment size ({}) must be at most as the number of symbols ({}), but his segment is longer: {}'.format(len(seg), len(symbols), seg))


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
        if symbol is UNKNOWN_FIELD:
            raise ValueError('Cannot use "{}" in the template.'.format(UNKNOWN_FIELD))
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
    board = board_from_template(BOARD_TEMPLATE, BOARD_SYMBOLS)
    print(board)


if __name__=="__main__":
    main()
