#!/usr/bin/env python3.6

'''Generator of sudoku boards of different size and difficulty. The
implementation is very UNOPTIMAL CPU and memory wise. In particular, it puts
large pressure on GC. A cache to lookup if an item has a know solution(s) would
dramatically improve performance.'''

import argparse
import collections
import itertools
import random
import string
import sys
import time

# Empty field is a placeholder in the template that is not a part of the Board.
EMPTY_FIELD = '.'

# Unknown value in a field.
UNKNOWN_FIELD = '-'

# Template of the board. "." stands for empty field
DEFAULT_TEMPLATE='''
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

DEFAULT_SYMBOLS = '123456789'

log_start_time = time.time()
rand = random.Random(0)


class Board:
    '''A Board contains information about size of the board, information about
    Sections and occupancies of the Fields. A Field is the smallest element of
    the Board. A Section is a collection of indexes of the Fields on the Board.
    To make a Board valid, all the Sections of the board are heterogenous. A
    Section is heterogenous if all the Fields of that Section are different, or
    empty. A Section is full if all the Fields of that Section are non-empty.
    '''

    def __init__(self, height, width, segments, symbols, all_coords=None, filled=None):
        '''segments are all the Segments composing the Board. The Board does
        not have notion of rows, colums or any kind of areas, only Segments.'''
        self.height, self.width = height, width
        self.segments = segments
        self.symbols = set(symbols)
        # Set of all the coordinates from all the segments.
        self._all_coords = self._get_all_coords_from_segments(segments) if all_coords is None else all_coords
        # Map of coordinates with values. Coordinates not in the map have
        # default value of UNKNOWN_FIELD. NOTE: this can be OPTIMIZED
        # memorywise, since the next board will copy this field.
        self._filled = {} if filled is None else filled

    def _get_all_coords_from_segments(self, segments):
        '''Return coordinates of all the fields form all the segments.'''
        return set(coord for seg in segments for coord in seg.coords)

    def get_area(self):
        return self.width * self.height

    def __str__(self):
        lines = [[EMPTY_FIELD] * self.width for _ in range(self.height)]
        for (i_row, i_col) in self._all_coords:
            symbol = self._filled.get((i_row, i_col), UNKNOWN_FIELD)
            lines[i_row][i_col] = symbol
        return '\n'.join(''.join(line) for line in lines)

    def iter_next_boards(self):
        '''Iterate on the "next" boards w.r.t. to the current one. A next board
        is a board with a next field filled with one of the symbols. The next
        boards are not necessarily valid.'''
        next_keys = self._all_coords - self.get_filled_fields()
        if not next_keys:
            return
        next_field = sorted(next_keys)[0]
        # Without shuffling the boards are repetitive and boring.
        next_symbols = shuffle(self.symbols)
        for symbol in next_symbols:
            yield self._copy_and_set(next_field, symbol)
    
    def _copy_and_set(self, coord, symbol):
        '''Copies the current board and sets the symbol in the place indicated
        by coord.'''
        if coord in self._filled:
            raise ValueError('Coord {} already filled with value "{}", tried to overwrite with "{}'.format(coord, self._filled[coord], symbol))
        if coord not in self._all_coords:
            raise ValueError('coordinate {} is not on the board'.format(coord))
        if symbol not in self.symbols:
            raise ValueError('bad symbol: {}'.format(symbol))
        new_filled=self._filled.copy()
        new_filled[coord] = symbol
        return Board(height=self.height,
                     width=self.width,
                     segments=self.segments,
                     symbols=self.symbols,
                     all_coords=self._all_coords,
                     filled=new_filled)

    def copy_and_remove(self, coord):
        '''Copies the board and removes a symbol at coord.'''
        if coord not in self._filled:
            raise ValueError('Coord to remove {} not filled'.format(coord))
        new_filled=self._filled.copy()
        del new_filled[coord]
        return Board(height=self.height,
                     width=self.width,
                     segments=self.segments,
                     symbols=self.symbols,
                     all_coords=self._all_coords,
                     filled=new_filled)


    def is_full(self):
        '''Check if the board has all the fields filled. It does not mean that
        it is valid.'''
        return len(self._all_coords) == len(self._filled)

    def is_valid(self):
        '''Check if the board is valid. A valid board is a board with no
        repeated values per segment. A valid board does not imply that the
        board is complete. To be complete, the board must be valid and full.'''
        # NOTE: this is not optimal. It checks all the segments. It would be
        # sufficient to check the affected segments during _copy_and_set
        # operation.
        for seg in self.segments:
            if not self._is_segment_valid(seg):
                return False
        return True

    def _is_segment_valid(self, segment):
        symbols_so_far = set()
        for coord in segment.coords:
            symbol = self._filled.get(coord)
            if symbol is None:
                continue
            if symbol in symbols_so_far:
                return False
            symbols_so_far.add(symbol)
        return True

    def get_filled_fields(self):
        return self._filled.keys()


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
        raise ValueError('Rows have different lenghts. Lengths: {}. Didn\'t you forget to use EMPTY_FIELD symbol "{}"?'.format(widths, EMPTY_FIELD))
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


def drill_board(initial_board, cutoff):
    '''Drill holes in the board. That is, remove fields from the board until
    there is no unique solution. It may never stop (must be terminated by hand).'''
    backlog = collections.deque([initial_board])
    min_board = initial_board
    while backlog:
        board = backlog.pop()
        if not has_unique_solution(board):
            # The board does not have unique solution, so we discard it.
            continue
        if len(board.get_filled_fields()) < len(min_board.get_filled_fields()):
            # Store the board with that has the least number of fields filled,
            # but still has minimal solution.
            fillness = float(len(board.get_filled_fields()))/board.get_area()
            log('drill backlog {}, score {} {:.1f}%'.format(len(backlog), len(board.get_filled_fields()), fillness * 100.0))
            min_board = board
            if fillness <= cutoff:
                break
        for field_to_remove in shuffle(board.get_filled_fields()):
            new_board = board.copy_and_remove(field_to_remove)
            backlog.append(new_board)
    return min_board


def has_unique_solution(board):
    it = backtrack_solutions(board)
    next(it)
    try:
        next(it)
    except StopIteration:
        # Backtracking will break at second next() because there is no next
        # solution.
        return True
    # If the backtracking didn't fail, then it means that there are at least
    # two other solutions.
    return False


# Given a board, iterate through the solutions.
def backtrack_solutions(initial_board):
    backlog = collections.deque([initial_board])
    while backlog:
        board = backlog.pop()
        signature=str(board)
        if not board.is_valid():
            continue
        if board.is_full():
            yield board
        backlog.extend(board.iter_next_boards())


def shuffle(coll):
    shuffled = list(coll)
    rand.shuffle(shuffled)
    return shuffled


def load_template_file(path):
    n_symbols = 9
    with open(path) as h:
        lines = [s.strip() for s in h]
    for s in lines:
        if s.startswith('# n_symbols'):
            n_symbols = int(s.split(' ')[2])
    template_lines = [s for s in lines if not s.startswith('#')]
    template = '\n'.join(template_lines)
    symbols = string.hexdigits[:n_symbols]
    return template, symbols


def log(message):
    dt = time.time() - log_start_time
    print('{:.1f}\t{}'.format(dt, message), file=sys.stderr)


def get_options():
    p = argparse.ArgumentParser(description='sudoku generator')
    p.add_argument('-t', '--template', dest='template_file',
                   help='path to template file')
    p.add_argument('-c', '--cutoff', dest='cutoff', type=float, default=0.50,
                   help='cutoff threshold of filled fields to stop looking for solution')
    return p.parse_args()

def main():
    opts = get_options()
    log('Initializing board')
    if opts.template_file is None:
        template = DEFAULT_TEMPLATE
        symbols = DEFAULT_SYMBOLS
    else:
        template, symbols = load_template_file(opts.template_file)
    log('Template ({}):\n{}'.format(opts.template_file, template))
    log('Symbols: {}'.format(symbols))
    initial_board = board_from_template(template, symbols)
    log('Find first solution')
    board = next(backtrack_solutions(initial_board))
    log('Got first solution, will remove fields')
    drilled_board = drill_board(board, cutoff=opts.cutoff)
    print(drilled_board)



if __name__=="__main__":
    main()
