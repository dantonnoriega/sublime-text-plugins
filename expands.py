import sublime, sublime_plugin

class ExpandSelectionToEofCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        v = self.view
        s = v.sel()
        eof = v.size()

        first_point = v.line(s[0]).a
        region_to_eof = sublime.Region(first_point, eof)
        s.clear()
        s.add(region_to_eof)

class ExpandSelectionToSectionCommand(sublime_plugin.TextCommand):
    def run(self, edit):

        v = self.view
        s = v.sel()

        def get_text(row, col):
            return v.substr(v.line(v.text_point(row, col)))

        def find_top(line, pattern):
            # print('%d' % line)
            if pattern.match(get_text(line, 0)): # match text
                top = v.line(v.text_point(line + 1, 0))
                # print('section values: (%d, %d)' % (top.a, top.b))
                return top
            else:
                return find_top(line - 1, pattern)

        def find_bottom(line, eof_line_num, pattern):
            # print('%d' % line)
            if pattern.match(get_text(line, 0)): # match text
                bottom = v.line(v.text_point(line - 1, 0))
                # print('section values: (%d, %d)' % (bottom.a, bottom.b))
                return bottom
            elif line == eof_line_num:
                bottom = v.line(v.text_point(eof_line_num, 0))
                # print('eof values: (%d, %d)' % (bottom.a, bottom.b))
                return bottom
            else:
                return find_bottom(line + 1, eof_line_num, pattern)

        # find pattern
        import re
        pattern = re.compile("^[ ]*# [#]{4,}|^[ ]*[#]{4,}|^[ ]*#+ [\w]+.+[-]+$|^`{3}")

        # search for closest section top and bottom
        first_point = v.line(s[0]).a
        current_line = v.rowcol(first_point)[0] # get line number
        eof = v.size()
        eof_line_num = v.rowcol(eof)[0]
        top_line = find_top(current_line, pattern)
        bottom_line = find_bottom(current_line, eof_line_num, pattern)
        section = sublime.Region(top_line.a, bottom_line.b)

        s.clear()
        s.add(section)


class SendMagrittrPipe(sublime_plugin.TextCommand):

    def move_cursor(self, line_num):
        """move cursor to the left of line"""
        v = self.view
        v.sel().clear()
        region = v.line(v.text_point(line_num, 0))
        v.sel().add(region.begin())
        return v.sel()

    def run(self, edit):

        v = self.view
        s = v.sel()

        def get_text(row, col):
            return v.substr(v.line(v.text_point(row, col)))

        def find_pipe(line, pattern):
            text = get_text(line, 0)
            #check
            print(text)
            print(pattern.search(text))
            if pattern.search(text) is None:
                return None

            if pattern.search(text): # search text
                top = v.line(v.text_point(line, 0))
                # print('section values: (%d, %d)' % (top.a, top.b))
                return top
            else:
                return None

        def find_end_pipe(line, eof_line_num, pattern):
            line = line + 1
            # print('CURRENT BOTTOM LINE: %d' % line)
            text = get_text(line, 0)

            #check
            print(text)
            if pattern.search(text): # search text
                bottom = v.line(v.text_point(line, 0))
                # print('section values: (%d, %d)' % (bottom.a, bottom.b))
                return bottom
            elif line == eof_line_num:
                bottom = v.line(v.text_point(eof_line_num, 0))
                # print('eof values: (%d, %d)' % (bottom.a, bottom.b))
                return bottom
            else:
                return find_end_pipe(line, eof_line_num, pattern)

        # find pattern
        import re
        re_pipe = re.compile("%<?>%[ ]*$")
        re_end_pipe = re.compile("[^%][ ]*$")

        # search for closest section top and bottom
        initial_selection = s[0]
        first_point = v.line(s[0]).a
        current_line_num = v.rowcol(first_point)[0] # get line number
        # print('CURRENT LINE: %d' % current_line_num)
        eof = v.size()
        eof_line_num = v.rowcol(eof)[0]
        # print('EOF LINE: %d' % eof_line_num)
        top_pipe_line = find_pipe(current_line_num, re_pipe)
        bottom_pipe_line = find_end_pipe(current_line_num, eof_line_num, re_end_pipe)

        # check if top_pipe_line is empty. If so, run send_text_plus on line.
        if top_pipe_line is None:
            # Add selection
            line_text = v.line(v.text_point(current_line_num, 0))
            s.add(line_text)
            # Run command from Enhanced-R
            v.run_command('send_text_plus')
            s.subtract(line_text)
            self.move_cursor(current_line_num + 1)
        else:
            bottom_pipe_line_num = v.rowcol(bottom_pipe_line.a)[0] # get line number
            chunk_range = sublime.Region(top_pipe_line.a, bottom_pipe_line.b)

            # # Add selection
            s.add(chunk_range)

            # print("send chunk:\n%s" % self.view.substr(chunk_range))

            # Run command from Enhanced-R
            v.run_command('send_text_plus')

            # Restore initial selection
            s.subtract(chunk_range)

            #move cursor
            # print("RETURN BOTTOM LINE + 1: %d" % (bottom_pipe_line_num + 1))
            self.move_cursor(bottom_pipe_line_num + 1)

