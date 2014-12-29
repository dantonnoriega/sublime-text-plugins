"""
DESCRIPTION:
Using SublimeREPL, this plugin allows one to easily transfer AND
evaluate blocks of python code. The code automatically detect python
blocks, executes them, and skips white space, comment blocks and
comment lines.

REQUIRES:
working with only 2 groups in the window. the main group (group 0)
needs to be your scripts and the second group (group 1) needs to be
a repl window.

keybind the following commands:
    py_col
        - used to open up a python repl as a group ("group" : 1) in
        the same window, column-wise. useful for full-screen work with
        scripts in the main group and repl in the other.
    py_row
        - same as py_col, but as a row. best for working while also using
        part of the screen for a browser.
    repl_trans_and_eval
        - workhorse script. it will automatically transfer lines or blocks
        of code to repl, execute them, move the cursor down, and refocus
        back on the script group.
"""

import sublime, sublime_plugin

# create column group
class PyColCommand(sublime_plugin.WindowCommand):
    def run(self):
        self.window.run_command('set_layout', {
            "cols": [0.0, 0.5, 1.0],
            "rows": [0.0, 1.0],
            "cells": [[0, 0, 1, 1], [1, 0, 2, 1]]
        })
        self.window.run_command('run_existing_window_command', {
            "id": "repl_python_ipython",
            "file": "config/Python/Main.sublime-menu"
        })
        self.window.run_command('move_to_group', {"group": 1})

# create row group
class PyRowCommand(sublime_plugin.WindowCommand):
    def run(self):
        self.window.run_command('set_layout', {
            "cols":[0.0, 1.0],
            "rows":[0.0, 0.5, 1.0],
            "cells":[[0, 0, 1, 1], [0, 1, 1, 2]]
        })
        self.window.run_command('run_existing_window_command', {
            "id": "repl_python_ipython",
            "file": "config/Python/Main.sublime-menu"
        })
        self.window.run_command('move_to_group', {"group": 1})

# transfer and evaluate
class ReplTransAndEvalCommand(sublime_plugin.TextCommand):

    def run(self, edit):
        # get largest selected point and eof
        v = self.view
        lines = v.lines(v.sel()[0]) # get lines without newline breaks
        max_point = lines[len(lines) - 1].end() # largest selected non newline point
        max_point_line_num = v.rowcol(max_point)[0] # line num of max point
        eof_line = v.rowcol(v.size())[0] # get the eof line
        block = True if len(v.lines(v.sel()[0])) > 1 else False # tag blocks of code

        ## order and remove blocked comments and empty space
        ##  from selection (keep only code blocks)
        self.keep_code_blocks()

        ## NOTE: anything printed is sent to the sublime console (ctrl+`)
        ##  which is useful for understanding whats happening.
        if v.line(max_point).empty() and block:
            print('multiple blocks')

        # send lines to REPL
        v.window().run_command('repl_transfer_current', {
            "scope": "lines",
            "action": "view_write"
        })
        v.window().run_command('focus_group', {"group": 1}) # focus REPL
        v.window().run_command('repl_enter') # evaluate code

        # collapse cursors to last point of original selection
        v.sel().clear()
        v.sel().add(max_point)

        ## check if single block or line of code. eval accordingly
        if not v.line(max_point).empty() and block:
            print('single block')
            v.window().run_command('repl_enter')
            max_point_line_num = self.move_down(max_point_line_num)

            # run through whitespace if finished block
            if v.line(v.sel()[0]).empty():
                print('block finished')
                self.clear_whitespace(max_point_line_num, eof_line)
            else:
                print('still in block')
        elif not v.line(max_point).empty() and not block:
            print('one line')
            max_point_line_num = self.move_down(max_point_line_num)
        else:
            if not block:
                print('empty line')

            # run through whitespace if empty line
            if v.line(v.sel()[0]).empty():
                self.clear_whitespace(max_point_line_num, eof_line)

        # focus back to scripts
        v.window().run_command('focus_group', {"group": 0})

    def move_down(self, line_num):
        """move cursor down one line and to far left"""
        v = self.view
        v.sel().clear()
        line_num = line_num + 1
        region = v.line(v.text_point(line_num, 0))
        v.sel().add(region.begin())
        return line_num

    def clear_whitespace(self, line_num, eof_line):
        """move cursor through whitespace without evaluating"""
        v = self.view
        # clear whitespace
        if v.line(v.sel()[0]).empty():
            print('clearing whitespace')

        while v.line(v.sel()[0]).empty():
            line_num = self.move_down(line_num)
            if line_num >= eof_line:
                break
        print('------\n')

    def keep_code_blocks(self):
        """ find and skip any comment blocks or comment lines, isolating
        blocks of code """
        selection = self.view.line(self.view.sel()[0]) # get the region, ordered

        # find points of three quotes contained in the selection
        three_quotes_pattern = self.view.find_all('(\"\"\")')
        three_quotes = [q for q in three_quotes_pattern if selection.contains(q)]

        # find comment-only lines
        comment_pattern = self.view.find_all('^#.*')
        comment_lines = [q for q in comment_pattern if selection.contains(q)]

        # create blocks by finding three quote pairs
        def find_comment_blocks(list):
            start_points = []
            end_points = []

            for i, region in enumerate(three_quotes):
                if (i+1)%2 == 1:
                    start_points.append(region.a)
                else:
                    end_points.append(region.b)

            comment_blocks = []
            for val in zip(start_points, end_points):
                block = self.view.lines(sublime.Region(val[0], val[1]))
                comment_blocks.extend(block)

            return comment_blocks

        # get all lines and comment blocks
        all_selected_lines = self.view.lines(self.view.sel()[0])
        comment_blocks = find_comment_blocks(three_quotes)

        # create comment indeces
        comment_block_index = [x in comment_blocks for x in all_selected_lines]
        comment_line_index = [x in comment_lines for x in all_selected_lines]

        # removed comments
        index_val_tups = zip(all_selected_lines, comment_block_index,
            comment_line_index)
        comments_removed = [a for a, b, c in index_val_tups if b == c]

        # find empty lines and whitespace blocks. keep one space after blocks.
        empty_index = [x.empty() for x in comments_removed] # find empty lines
        whitespace_index = []
        for i, x in enumerate(empty_index):
            if x != empty_index[i-1]:
                whitespace_index.append(False)
            else:
                whitespace_index.append(x)

        # remove whitespace (any empty lines not immediately after block)
        keep_lines = [a for a,b in
            zip(comments_removed, whitespace_index) if not b]

        self.view.sel().clear() # clear current unordered selection
        self.view.sel().add_all(keep_lines) # add all isolated blocks

        return self.view.sel()
