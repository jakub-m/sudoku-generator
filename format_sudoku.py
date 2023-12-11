#!/usr/bin/env python3


import argparse
import collections
import json
import string
import sys

Sudoku = collections.namedtuple('Sudoku', 'template board width height')

EMPTY_CELL = u'-'

HTML_HEADER='''
<!DOCTYPE html>
<html>
    <head>
        <style>
            body {
                 -webkit-print-color-adjust: exact;
            }
            div {
                padding: 0;
                margin: 0;
            }
            .f {
                font-family: Helvetica;
                font-size: 30px;
                font-style: bold;

                height: 60px;
                width:  60px;
                line-height: 60px;
                text-align: center;
                vertical-align: middle;
                float:left;
                border-right: 2px dotted #ddd;
                border-bottom: 2px dotted #ddd;
            }
            .start_line {
                clear:both;
                border-left: 3px dotted #ddd;
            }
            .border_top {
                border-top: 3px solid black !important;
            }
            .border_right {
                border-right: 3px solid black !important;
            }
            .border_left {
                border-left: 3px solid black !important;
            }
            .border_bottom {
                border-bottom: 3px solid black !important;
            }
        </style>
    </head>
    <body>
'''

HTML_FOOTER='''
    </body>
</html>
'''

class ValueConverter(object):
    '''A function that consistently maps input to output.'''
    def __init__(self, values):
        assert len(set(values)) == len(values), 'Values should be unique, but are: ' + str(values)
        self._unused_values = list(values)
        self._map = {}

    def __call__(self, _input):
        if _input == EMPTY_CELL:
            return ''
        if _input not in self._map:
            try:
                self._map[_input] = self._unused_values[0]
            except IndexError:
                raise IndexError('No enough values! Try different value set.')
            self._unused_values = self._unused_values[1:]
        return self._map[_input]


def print_header():
    print(HTML_HEADER)


def print_footer():
    print(HTML_FOOTER)


def parse_board_from_lines(lines):
    '''Return map of (row, column): value. Input is a single string with board,
    where lines are separated with NL.'''
    return dict(_iter_parse_board_from_lines(lines))


def _iter_parse_board_from_lines(lines):
    striped_lines = (s.strip() for s in lines.split())
    for i_row, row in enumerate(striped_lines):
        for i_col, value in enumerate(row):
            yield ((i_row, i_col), value)


def validate_board(board, width, height):
    for i_row in range(height):
        for i_col in range(width):
            d = (i_row, i_col)
            assert d in board, '{} not in board'.format(d)
    assert len(board) == (width * height), 'bad board size, should be {}'.format(width * height)


def print_cells(sudoku, printable_mapper):
    '''printable_mapper is a function that maps value from board to a printable value'''
    board = parse_board_from_lines(sudoku.board)
    template = parse_board_from_lines(sudoku.template)
    validate_board(board, width=sudoku.width, height=sudoku.height)
    validate_board(template, width=sudoku.width, height=sudoku.height)
    for i_row in range(sudoku.height):
        top_line = (i_row == 0)
        for i_col in range(sudoku.width):
            class_map = {
                'start_line': (i_col == 0),
                'border_left': (i_col == 0),
                'border_top': (i_row == 0),
                'border_right': has_border(template, (i_row, i_col), (i_row, i_col+1)),
                'border_bottom': has_border(template, (i_row, i_col), (i_row+1, i_col)),
            }
            classes = sorted(k for k in class_map if class_map[k])
            board_value = board[(i_row, i_col)]
            printable_value = printable_mapper(board_value)
            _print_cell(printable_value, classes)


def has_border(dic, key_ref, key_other):
    assert key_ref in dic
    return (key_other not in dic) or dic[key_ref] != dic[key_other]


def _print_cell(value, classes):
    classes = ['f'] + classes
    print('<div class="{_classes}">{_value}</div>'.format(_classes=' '.join(classes),
                                                          _value=value))


def get_options():
    p = argparse.ArgumentParser(description='Sudoku formatter')
    p.add_argument('-j', '--json', dest='json_path', help='JSON file with sudoku board')
    p.add_argument('-s', '--value-set', dest='value_set', choices=['0', '1', 'a', 'A'], default='1',
                   help='set of values')
    return p.parse_args()


def main():
    opts = get_options()
    with open(opts.json_path) as h:
        sudoku = Sudoku(**json.load(h))
    value_converter = ValueConverter({
        '0': string.hexdigits,
        '1': string.hexdigits[1:],
        'a': string.ascii_lowercase,
        'A': string.ascii_uppercase
        }[opts.value_set])
    sys.stderr.write('{}\n\n{}\n\n'.format(sudoku.template, sudoku.board))
    print_header()
    print_cells(sudoku, value_converter)
    print_footer()

if __name__=="__main__":
    main()
