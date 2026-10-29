#!/usr/bin/env python3
"""Render a benchmark-searcher Markdown table as a self-contained HTML report."""

import argparse
import html
from pathlib import Path
import re
from urllib.parse import quote, urlsplit


def inline(value):
    pattern = r"\[([^\]]+)\]\((https?://[^)]+)\)|\*\*(.+?)\*\*|`([^`]+)`|<br\s*/?>"
    output = []
    position = 0
    for match in re.finditer(pattern, value):
        output.append(html.escape(value[position:match.start()]))
        label, url, bold, code = match.groups()
        if url:
            parsed = urlsplit(url)
            if not parsed.hostname:
                raise ValueError(f"Invalid source URL: {url}")
            output.append(f'<a href="{html.escape(url, quote=True)}" target="_blank" rel="noopener noreferrer">{html.escape(label)}</a>')
        elif bold:
            output.append(f'<strong>{html.escape(bold)}</strong>')
        elif code:
            output.append(f'<code>{html.escape(code)}</code>')
        else:
            output.append('<br>')
        position = match.end()
    output.append(html.escape(value[position:]))
    return ''.join(output).replace(r'\|', '|')


def prose(lines):
    blocks = []
    for block in '\n'.join(lines).strip().split('\n\n'):
        if not block.strip():
            continue
        if block.startswith('## '):
            blocks.append('<h2>' + inline(block[3:]) + '</h2>')
        else:
            blocks.append('<p>' + inline(block.replace('\n', ' ')) + '</p>')
    return '\n'.join(blocks)


def render(source, destination):
    lines = source.read_text().splitlines()
    indices = [i for i, line in enumerate(lines) if line.startswith('| ')]
    if len(indices) < 3 or indices != list(range(indices[0], indices[-1] + 1)):
        raise ValueError('Expected one contiguous Markdown table with at least one benchmark.')
    table = [[cell.strip() for cell in re.split(r'(?<!\\)\|', lines[i].strip())[1:-1]] for i in indices]
    headers, separator, *rows = table
    if len(headers) != 9 or any(len(row) != len(headers) for row in table):
        raise ValueError('Expected nine columns in every table row.')
    if not all(re.fullmatch(r':?-+:?', cell) for cell in separator):
        raise ValueError('Invalid Markdown table separator.')
    title = next(line[2:] for line in lines[:indices[0]] if line.startswith('# '))
    intro = [line for line in lines[:indices[0]] if not line.startswith('# ')]
    header_html = ''.join(f'<th scope="col"><span>{inline(value)}</span><button class="resize" type="button" aria-label="Resize {html.escape(value, quote=True)} column; use left and right arrow keys"></button></th>' for value in headers)
    rendered_rows = []
    for row in rows:
        cells = []
        for i, value in enumerate(row):
            tag = 'th' if i == 0 else 'td'
            attributes = ' scope="row"' if i == 0 else ''
            cells.append(f'<{tag}{attributes}>{inline(value)}</{tag}>')
        rendered_rows.append('<tr>' + ''.join(cells) + '</tr>')
    row_html = '\n'.join(rendered_rows)
    template = (Path(__file__).resolve().parent.parent / 'assets' / 'report.html').read_text()
    replacements = {
        '@@TITLE@@': html.escape(title),
        '@@INTRO@@': prose(intro),
        '@@COLS@@': '<col>' * len(headers),
        '@@HEADERS@@': header_html,
        '@@ROWS@@': row_html,
        '@@FOOTER@@': prose(lines[indices[-1] + 1:]),
        '@@SOURCE@@': quote(source.name),
        '@@COUNT@@': str(len(rows)),
    }
    for key, value in replacements.items():
        template = template.replace(key, value)
    destination.write_text(template)
    print(f'Rendered {len(rows)} benchmarks to {destination}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    source = args.source.resolve()
    render(source, (args.output or source.with_suffix('.html')).resolve())
