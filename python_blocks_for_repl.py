"""
DESCRIPTION:
Using SublimeREPL, this plugin allows one to easily transfer AND
evaluate blocks of python code. The code automatically detect python
blocks, executes them, and skips space, comment blocks and
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

        # check if one line or a block
        one_line = True if len(v.lines(v.sel()[0])) == 1 else False # tag if one line

        # get all selected lines and find maximal point and line
        all_selected = self.keep_code_blocks(v.sel()[0])
        lines = v.lines(v.sel()[0]) # get selected line(s) without newline breaks
        max_point = lines[len(lines) - 1].end() # largest selected non newline point
        eof_line = v.rowcol(v.size())[0] # line num of max point

        # get line nums for all code blocks and empty indeces
        all_code = v.line(sublime.Region(0, v.size()))
        cleaned_lines = self.keep_code_blocks(all_code) # get all lines w/o comments
        line_ref = [v.rowcol(x.begin())[0] for x in cleaned_lines]
        empty_index, block_end_index, block_index = self.get_indeces(cleaned_lines)
        line_empty_ref = dict((k, v) for k, v in zip(line_ref, empty_index) if v)
        line_block_end_ref = dict((k, v) for k, v in zip(line_ref, block_end_index) if v)
        line_block_ref = dict((k, v) for k, v in zip(line_ref, block_index) if v)

        ## to see what's happening
        # print('line ref      ', line_ref)
        # print('empty ref     ', line_empty_ref)
        # print('block ref     ', line_block_ref)
        # print('block end ref ', line_block_end_ref)

        # trims selection to code blocks
        v.sel().clear()
        v.sel().add_all(all_selected)

        # capture current or last line from max_point
        current_line_num = v.rowcol(max_point)[0]
        current_line = v.line(max_point)

        ## evaluate by line or blocks
        if not one_line: # if not one line
            # send lines to REPL
            v.window().run_command('repl_transfer_current', {
                "scope": "lines",
                "action": "view_write"
            })
            v.window().run_command('focus_group', {"group": 1}) # focus REPL
            v.window().run_command('repl_enter') # evaluate code

            # update current line
            current_line_num = current_line_num + 1

            # clear console
            if current_line_num in line_block_end_ref:
                v.window().run_command('repl_enter') # evaluate code
            elif current_line_num not in line_ref:
                v.window().run_command('repl_enter') # evaluate code
            else:
                pass

            # move cursor
            v.window().run_command('focus_group', {"group": 0}) # focus REPL
            self.move_cursor(current_line_num)

        else:
            if current_line_num in line_ref:

                print('run line %d: %s' % (current_line_num, v.substr(current_line)))
                v.window().run_command('repl_transfer_current', {
                    "scope": "lines",
                    "action": "view_write"
                }) # send lines to REPL
                v.window().run_command('focus_group', {"group": 1}) # focus REPL
                v.window().run_command('repl_enter')

                # update current line
                current_line_num = current_line_num + 1

                # move cursor down
                v.window().run_command('focus_group', {"group": 0}) # focus REPL
                self.move_cursor(current_line_num)
            else:
                # if line is empty or comment, then move cursor down
                # move cursor
                current_line_num = self.skip_lines(current_line_num, eof_line, line_ref)
                v.window().run_command('focus_group', {"group": 0}) # focus REPL
                self.move_cursor(current_line_num)

    def move_cursor(self, line_num):
        """move cursor to the left of line"""
        v = self.view
        v.sel().clear()
        region = v.line(v.text_point(line_num, 0))
        v.sel().add(region.begin())
        return v.sel()

    def skip_lines(self, line_num, eof_line, line_ref):
        """move cursor through empty lines or comments without evaluating"""

        if line_num not in line_ref:
            print('skipping lines')

            while line_num not in line_ref:
                if line_num > eof_line:
                    break
                line_num = line_num + 1

            print('------\n')
        else:
            pass

        return line_num

    def get_indeces(self, ordered_lines):
        """get indeces for blocks and for empty lines"""
        v = self.view

        #find empty lines and tab counts.
        # keep one space after blocks any code blocks.
        tab_size = 4
        empty_index = [x.empty() for x in ordered_lines] # find empty lines
        nonempty_index = [not x for x in empty_index]
        tab_count = [v.substr(x).count(' '*tab_size) for x in ordered_lines]
        text_tab = list(zip(nonempty_index, tab_count))

        # create a block index using tabs and nonempty_index
        carry_val = 0
        tab_count_filled = []
        for a, b in text_tab[::-1]: # key is to reverse vector THEN carry forward
            if a: # if we see a tab, carry tab count forward
                carry_val = b
                tab_count_filled.append(carry_val)
            else: # else just assign curry value
                tab_count_filled.append(carry_val)

        tab_count_filled = tab_count_filled[::-1] # reverse again to get correct order
        block_index = [x > 0 or y for x, y in zip(tab_count_filled, nonempty_index)]

        # find when a block ends
        block_end_index = []
        for i, x in enumerate(tab_count_filled):
            block_end_index.append(True if (x == 0 and x < tab_count_filled[i-1]) else False)

        ## see what's happening
        # print('nonempty_index  ', [int(x) for x in nonempty_index])
        # print('tab_count       ', tab_count)
        # print('tab_count_filled', tab_count_filled)
        # print('block_end_index ', [int(x) for x in block_end_index])
        # print('block_index     ', [int(x) for x in block_index])
        # print('empty_index     ', [int(x) for x in empty_index])

        return (empty_index, block_end_index, block_index)

    def keep_code_blocks(self, selection):
        """remove unwanted lines and keep only code blocks"""
        v = self.view

        comments_removed = self.remove_comments(selection)
        keep_code_blocks = self.remove_empty_lines(comments_removed)

        return keep_code_blocks

    def remove_empty_lines(self, selection):
        """find and remove empty lines but keep end of comment blocks"""

        # find empty lines
        empty_index, block_end_index, block_index = self.get_indeces(selection)

        # # removed empty lines
        index_val_tups = zip(selection, empty_index, block_end_index)
        empty_lines_removed = [a for a, b, c in index_val_tups if not b or c]

        return empty_lines_removed

    def remove_comments(self, selection):
        """ find and skip any comment blocks or comment lines"""
        v = self.view

        def find_matches(pattern):
            find_all_matches = v.find_all(pattern)
            find_contained_matches = [q for q in find_all_matches if selection.contains(q)]
            return find_contained_matches

        def find_comment_blocks(regions):
            start_points = []
            end_points = []

            for i, region in enumerate(regions):
                if (i+1)%2 == 1:
                    start_points.append(region.a)
                else:
                    end_points.append(region.b)

            comment_blocks = []
            for val in zip(start_points, end_points):
                block = v.lines(sublime.Region(val[0], val[1]))
                comment_blocks.extend(block)

            return comment_blocks

        # find points of three quotes contained in the selection
        three_quotes = find_matches('(\"\"\")')

        # find full comment-only lines
        comment_lines = find_matches('^([ ]*#.*)')

        # create blocks by finding three quote pairs
        ordered_lines = v.lines(selection) # ensure selection is ordered
        comment_blocks = find_comment_blocks(three_quotes)

        # create comment indeces for each seperate line
        comment_block_index = [x in comment_blocks for x in ordered_lines]
        comment_line_index = [x in comment_lines for x in ordered_lines]

        # removed unwanted lines
        index_val_tups = zip(ordered_lines, comment_block_index,
            comment_line_index)
        comments_removed = [a for a, b, c in index_val_tups if b == c]

        return comments_removed

