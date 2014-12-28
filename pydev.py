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

class ReplViewAndExecute(sublime_plugin.TextCommand):

    def run(self, edit):
        # get largest selected point and eof
        v = self.view
        lines = v.lines(v.sel()[0]) # get lines without newline breaks
        max_point = lines[len(lines) - 1].end() # largest selected non newline point
        max_point_line_num = v.rowcol(max_point)[0] # line num of max point
        eof_line = v.rowcol(v.size())[0] # get the eof line
        block = True if len(v.lines(v.sel()[0])) > 1 else False # find how many lines were selected

        # order and remove blocked comments and empty space (keep only code blocks)
        self.keep_code_blocks()

        if v.line(max_point).empty() and block:
            print('multiple blocks')
        else:
            print('one line')


        v.window().run_command('repl_transfer_current', {
            "scope": "lines",
            "action": "view_write"
        }) # send lines to REPL
        v.window().run_command('focus_group', {"group": 1}) # focus REPL
        v.window().run_command('repl_enter')
        v.sel().clear()
        v.sel().add(max_point)

        # check block if ended on non empty line
        if not v.line(max_point).empty() and block:
            print('single block')
            v.window().run_command('repl_enter')
            max_point_line_num = self.move_down(max_point_line_num)

            # clear console if empty line
            if v.line(v.sel()[0]).empty():
                print('block finished, clear console')
                v.window().run_command('repl_enter')

                # clear whitespace
                self.clear_whitespace(max_point_line_num, eof_line)
            else:
                print('still in block')
        elif not v.line(max_point).empty() and not block:
            max_point_line_num = self.move_down(max_point_line_num)
        else:
            print('empty line')
            # clear console if empty line
            if v.line(v.sel()[0]).empty():
                self.clear_whitespace(max_point_line_num, eof_line)

        # focus console
        v.window().run_command('focus_group', {"group": 0})

    def move_down(self, line_num):
        v = self.view
        v.sel().clear()
        line_num = line_num + 1
        region = v.line(v.text_point(line_num, 0))
        v.sel().add(region.begin())
        return line_num

    def clear_whitespace(self, line_num, eof_line):
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
        comments_removed = [a for a,b,c
            in zip(all_selected_lines, comment_block_index,
            comment_line_index) if b == c]

        # find empty lines and whitespace blocks
        empty_index = [x.empty() for x in comments_removed] # find empty lines
        whitespace_index = []
        for i, x in enumerate(empty_index):
            if x != empty_index[i-1]:
                whitespace_index.append(False)
            else:
                whitespace_index.append(x)

        # remove whitespace
        keep_lines = [a for a,b
            in zip(comments_removed, whitespace_index) if not b]

        # print('comment blocks:\n%s' % comment_block_index)
        # print('comment lines:\n%s' % comment_line_index)
        # print('keep the following lines:\n%s' % comments_removed)
        # print('empty lines:\n%s' % empty_index)
        # print('whitespace lines:\n%s' % whitespace_index)

        self.view.sel().clear() # clear current unordered selection
        self.view.sel().add_all(keep_lines)

        return self.view.sel()













