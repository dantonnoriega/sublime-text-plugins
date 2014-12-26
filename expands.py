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
            top = None
            while top is None:
                line = line - 1
                if pattern.match(get_text(line, 0)): # match text
                    return v.line(v.text_point(line + 1, 0))

        def find_bottom(line, pattern):
            top = None
            while top is None:
                line = line + 1
                if pattern.match(get_text(line, 0)): # match text
                    return v.line(v.text_point(line - 1, 0))

        # find pattern
        import re
        pattern = re.compile("^[#]+.*[----]+$")

        # search for closest section top and bottom
        first_point = v.line(s[0]).a
        current_line = v.rowcol(first_point)[0] # get line number
        top_line = find_top(current_line, pattern)
        bottom_line = find_bottom(current_line, pattern)
        section = sublime.Region(top_line.a, bottom_line.b)

        s.clear()
        s.add(section)


