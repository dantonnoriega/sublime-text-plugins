import sublime, sublime_plugin

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

        def in_paren(line):
            text = get_text(line, 0)
            open_paren = re.compile("\([ ]*$|\([ ]+#+.*$")
            return open_paren.search(text)

        def next_pipe(line, pattern):
            text = get_text(line, 0)
            print(text)
            if pattern.search(text):
                return line
            else:
                return next_pipe(line + 1, pattern)

        def find_pipe(line, pattern):
            text = get_text(line, 0)
            #check
            print(text)
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
            print('CURRENT BOTTOM LINE NUM: %d' % line)
            text = get_text(line, 0)
            print(text)
            # if no pipe, then check for open parenthese
            if not pattern.search(text): # search text
                # if end in open parenth, keep searching until next pipe
                if in_paren(line):
                    print("IN PAREN.")
                    line = next_pipe(line, pattern)
                    print("END PAREN (FOUND PIPE). LINE NUM %s" % line)
                    return find_end_pipe(line, eof_line_num, pattern)
                else:
                    bottom = v.line(v.text_point(line, 0))
                    return bottom

            elif line == eof_line_num:
                bottom = v.line(v.text_point(eof_line_num, 0))
                return bottom
            else:
                return find_end_pipe(line, eof_line_num, pattern)


        # SEND SELECTION: if something is selected, send that, not the line
        if s[0].a != s[0].b:
            chunk_range = sublime.Region(s[0].a, s[0].b)
            print("SEND SELECTION:\n%s" % self.view.substr(chunk_range))
            # Run command from Enhanced-R
            v.run_command('send_text_plus')
            return

        # DEFINE PIPE PATTERN
        import re
        re_pipe = re.compile("(%<?>%)")

        # DEFINE VARIABLES
        initial_selection = s[0]
        first_point = v.line(s[0]).a
        current_line_num = v.rowcol(first_point)[0] # get line number
        next_line_num = current_line_num + 1
        print('TOP LINE: %s' % current_line_num)
        eof = v.size()
        eof_line_num = v.rowcol(eof)[0]

        # LOOK AHEAD FOR '<-' or '->': if next line has an assignment, then send current line
        re_assign = re.compile("(<-)|(->)")
        next_text = get_text(next_line_num, 0)

        if re_assign.search(next_text):
            # Add selection
            line_text = v.line(v.text_point(current_line_num, 0))
            print("SEND LINE:\n%s" % v.substr(sublime.Region(line_text.a, line_text.b)))
            s.clear()
            s.add(line_text)
            # Run command from Enhanced-R
            v.run_command('send_text_plus')
            s.subtract(line_text)
            self.move_cursor(current_line_num + 1)
            return

        # FIND TOP/BOTTOM LINES OF PIPE SEQUENCE
        top_pipe_line = find_pipe(current_line_num, re_pipe)
        bottom_pipe_line = find_end_pipe(current_line_num, eof_line_num, re_pipe)

        # check if top_pipe_line is empty. If so, run send_text_plus on line.
        if top_pipe_line is None:
            # Add selection
            line_text = v.line(v.text_point(current_line_num, 0))
            print("SEND LINE:\n%s" % v.substr(sublime.Region(line_text.a, line_text.b)))
            s.clear()
            s.add(line_text)
            # Run command from Enhanced-R
            v.run_command('send_text_plus')
            s.subtract(line_text)
            self.move_cursor(current_line_num + 1)
            return
        else:
            bottom_pipe_line_num = v.rowcol(bottom_pipe_line.a)[0] # get line number
            chunk_range = sublime.Region(top_pipe_line.a, bottom_pipe_line.b)

            # # Add selection
            s.add(chunk_range)

            print("SEND CHUNK:\n%s" % self.view.substr(chunk_range))

            # Run command from Enhanced-R
            v.run_command('send_text_plus')

            # Restore initial selection
            s.subtract(chunk_range)

            #move cursor
            # print("RETURN BOTTOM LINE + 1: %d" % (bottom_pipe_line_num + 1))
            self.move_cursor(bottom_pipe_line_num + 1)
            return