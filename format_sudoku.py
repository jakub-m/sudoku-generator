#!/usr/bin/env python2.7

'''Convert output of sudoku generator to printable html.'''


import collections
import json
import sys

Sudoku = collections.namedtuple('Sudoku', 'symbols template board width height')


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
                float:left;
                height: 60px;
                width:  60px;
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


def print_cells(sudoku):
    board = parse_board_from_lines(sudoku.board)
    template = parse_board_from_lines(sudoku.template)
    validate_board(board, width=sudoku.width, height=sudoku.height)
    validate_board(template, width=sudoku.width, height=sudoku.height)
    for i_row in range(sudoku.height):
        top_line = (i_row == 0)
        for i_col in range(sudoku.width):
            value = board[(i_row, i_col)]
            class_map = {
                'start_line': (i_col == 0),
                'border_left': (i_col == 0),
                'border_top': (i_row == 0),
                'border_right': has_border(template, (i_row, i_col), (i_row, i_col+1)),
                'border_bottom': has_border(template, (i_row, i_col), (i_row+1, i_col)),
            }
            classes = sorted(k for k in class_map if class_map[k])
            _print_cell(value, classes)


def has_border(dic, key_ref, key_other):
    assert key_ref in dic
    return (key_other not in dic) or dic[key_ref] != dic[key_other]


def _print_cell(value, classes):
    classes = ['f'] + classes
    print('<div class="{}">{}</div>'.format(' '.join(classes), value))


def main():
    json_fname = sys.argv[1]
    with open(json_fname) as h:
        sudoku = Sudoku(**json.load(h))
    sys.stderr.write('{}\n\n{}\n\n'.format(sudoku.template, sudoku.board))
    print_header()
    print_cells(sudoku)
    print_footer()

if __name__=="__main__":
    main()
