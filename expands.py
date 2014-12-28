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
            print('%d' % line)
            if pattern.match(get_text(line, 0)): # match text
                top = v.line(v.text_point(line + 1, 0))
                print('section values: (%d, %d)' % (top.a, top.b))
                return top
            else:
                return find_top(line - 1, pattern)

        def find_bottom(line, eof_line, pattern):
            print('%d' % line)
            if pattern.match(get_text(line, 0)): # match text
                bottom = v.line(v.text_point(line - 1, 0))
                print('section values: (%d, %d)' % (bottom.a, bottom.b))
                return bottom
            elif line == eof_line:
                bottom = v.line(v.text_point(eof_line, 0))
                print('eof values: (%d, %d)' % (bottom.a, bottom.b))
                return bottom
            else:
                return find_bottom(line + 1, eof_line, pattern)

        # find pattern
        import re
        pattern = re.compile("^[#]+.*[----]+$")

        # search for closest section top and bottom
        first_point = v.line(s[0]).a
        current_line = v.rowcol(first_point)[0] # get line number
        eof = v.size()
        eof_line = v.rowcol(eof)[0]
        top_line = find_top(current_line, pattern)
        bottom_line = find_bottom(current_line, eof_line, pattern)
        section = sublime.Region(top_line.a, bottom_line.b)

        s.clear()
        s.add(section)


