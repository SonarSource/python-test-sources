#!/usr/bin/env python
"""
A script to create C code-coverage reports based on the output of
valgrind's callgrind tool.

"""
from __future__ import division, absolute_import, print_function

import optparse
import os
import re
import sys
from xml.sax.saxutils import quoteattr, escape

try:
    import pygments
    if tuple([int(x) for x in pygments.__version__.split('.')]) < (0, 11):
        raise ImportError()
    from pygments import highlight
    from pygments.lexers import CLexer
    from pygments.formatters import HtmlFormatter
    has_pygments = True
except ImportError:
    print("This script requires pygments 0.11 or greater to generate HTML")
    has_pygments = False


class FunctionHtmlFormatter(HtmlFormatter):
    """Custom HTML formatter to insert extra information with the lines."""
    def __init__(self, lines, **kwargs):
        HtmlFormatter.__init__(self, **kwargs)
        self.lines = lines

    def wrap(self, source, outfile):
        for i, (c, t) in enumerate(HtmlFormatter.wrap(self, source, outfile)):
            as_functions = self.lines.get(i-1, None)
            if as_functions is not None:
                yield 0, ('<div title=%s style="background: #ccffcc">[%2d]' %
                          (quoteattr('as ' + ', '.join(as_functions)),
                           len(as_functions)))
            else:
                yield 0, '    '
            yield c, t
            if as_functions is not None:
                yield 0, '</div>'


class SourceFile:
    def __init__(self, path):
        self.path = path
        self.lines = {}

    def mark_line(self, lineno, as_func=None):
        line = self.lines.setdefault(lineno, set())
        if as_func is not None:
            as_func = as_func.split("'", 1)[0]
            line.add(as_func)

    def write_text(self, fd):
        source = open(self.path, "r")
        for i, line in enumerate(source):
            if i + 1 in self.lines:
                fd.write("> ")
            else:
                fd.write("! ")
            fd.write(line)
        source.close()

    def write_html(self, fd):
        source = open(self.path, 'r')
        code = source.read()
        lexer = CLexer()
        formatter = FunctionHtmlFormatter(
            self.lines,
            full=True,
            linenos='inline')
        fd.write(highlight(code, lexer, formatter))
        source.close()


class SourceFiles:
    def __init__(self):
        self.files = {}
        self.prefix = None

    def get_file(self, path):
        if path not in self.files:
            self.files[path] = SourceFile(path)
            if self.prefix is None:
                self.prefix = path
            else:
                self.prefix = os.path.commonprefix([self.prefix, path])
        return self.files[path]

    def clean_path(self, path):
        path = path[len(self.prefix):]
        return re.sub(r"[^A-Za-z0-9\.]", '_', path)

    def write_text(self, root):
        for path, source in self.files.items():
            fd = open(os.path.join(root, self.clean_path(path)), "w")
            source.write_text(fd)
            fd.close()

    def write_html(self, root):
        for path, source in self.files.items():
            fd = open(os.path.join(root, self.clean_path(path) + ".html"), "w")
            source.write_html(fd)
            fd.close()

        fd = open(os.path.join(root, 'index.html'), 'w')
        fd.write("<html>")
        paths = sorted(self.files.keys())
        for path in paths:
            fd.write('<p><a href="%s.html">%s</a></p>' %
                     (self.clean_path(path), escape(path[len(self.prefix):])))
        fd.write("</html>")
        fd.close()


def collect_stats(files, fd, pattern):
    # TODO: Handle compressed callgrind files
    line_regexs = [
        re.compile(r"(?P<lineno>[0-9]+)(\s[0-9]+)+"),
        re.compile(r"((jump)|(jcnd))=([0-9]+)\s(?P<lineno>[0-9]+)")
        ]

    current_file = None
    current_function = None
    for i, line in enumerate(fd):
        if re.match("f[lie]=.+", line):
            path = line.split('=', 2)[1].strip()
            if os.path.exists(path) and re.search(pattern, path):
                current_file = files.get_file(path)
            else:
                current_file = None
        elif re.match("fn=.+", line):
            current_function = line.split('=', 2)[1].strip()
        elif current_file is not None:
            for regex in line_regexs:
                match = regex.match(line)
                if match:
                    lineno = int(match.group('lineno'))
                    current_file.mark_line(lineno, current_function)


if __name__ == '__main__':
    parser = optparse.OptionParser(
        usage="[options] callgrind_file(s)")
    parser.add_option(
        '-d', '--directory', dest='directory',
        default='coverage',
        help='Destination directory for output [default: coverage]')
    parser.add_option(
        '-p', '--pattern', dest='pattern',
        default='numpy',
        help='Regex pattern to match against source file paths [default: numpy]')
    parser.add_option(
        '-f', '--format', dest='format', default=[],
        action='append', type='choice', choices=('text', 'html'),
        help="Output format(s) to generate, may be 'text' or 'html' [default: both]")
    (options, args) = parser.parse_args()

    files = SourceFiles()
    for log_file in args:
        log_fd = open(log_file, 'r')
        collect_stats(files, log_fd, options.pattern)
        log_fd.close()

    if not os.path.exists(options.directory):
        os.makedirs(options.directory)

    if options.format == []:
        formats = ['text', 'html']
    else:
        formats = options.format
    if 'text' in formats:
        files.write_text(options.directory)
    if 'html' in formats:
        if not has_pygments:
            print("Pygments 0.11 or later is required to generate HTML")
            sys.exit(1)
        files.write_html(options.directory)
