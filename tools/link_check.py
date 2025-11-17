#!/usr/bin/env python3
"""Simple local link checker for HTML files in the repo.

Checks href and src attributes that are local (not http(s) or data:, mailto:)
and reports any target files that do not exist on disk.
"""
import os
import sys
from html.parser import HTMLParser

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

class LinkCollector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        for key in ('href', 'src'):
            if key in attrs:
                self.links.append(attrs[key])


def is_external(link):
    if not link:
        return True
    l = link.strip()
    # Treat javascript: and other URL schemes as external (not file checks)
    if l.startswith(('http://', 'https://', '//', 'mailto:', 'tel:', 'data:', 'javascript:')):
        return True
    return False


def normalize_link(link, html_file_dir):
    # Remove any query or hash
    link = link.split('#', 1)[0].split('?', 1)[0]
    if not link:
        return None
    # If absolute path starting with '/', treat relative to repo root
    if link.startswith('/'):
        link = link.lstrip('/')
        return os.path.join(ROOT, link)
    # If starts with ./ or ../ or a filename, resolve relative to html file dir
    return os.path.normpath(os.path.join(html_file_dir, link))


def main():
    html_files = []
    for dirpath, dirnames, filenames in os.walk(ROOT):
        # skip .git and .venv
        if '.git' in dirpath.split(os.sep):
            continue
        if '.venv' in dirpath.split(os.sep):
            continue
        # skip backups folder (local site backups)
        if 'backups' in dirpath.split(os.sep):
            continue
        for f in filenames:
            if f.lower().endswith('.html'):
                html_files.append(os.path.join(dirpath, f))

    missing = []
    total_links = 0

    for html in sorted(html_files):
        with open(html, 'r', encoding='utf-8', errors='ignore') as fh:
            content = fh.read()
        parser = LinkCollector()
        parser.feed(content)
        html_dir = os.path.dirname(html)
        for link in parser.links:
            if is_external(link):
                continue
            total_links += 1
            resolved = normalize_link(link, html_dir)
            # Some links are to directories (e.g., /posts/), check index.html or the directory exists
            if resolved and os.path.isdir(resolved):
                # Accept directory if it contains an index.html
                index_path = os.path.join(resolved, 'index.html')
                if os.path.exists(index_path):
                    continue
                else:
                    missing.append((html, link, resolved))
            elif resolved and not os.path.exists(resolved):
                missing.append((html, link, resolved))

    print(f"Scanned {len(html_files)} HTML files and {total_links} local links.")
    if not missing:
        print("No broken local links found.")
        return 0
    print(f"Found {len(missing)} missing local link(s):")
    for html, link, resolved in missing:
        print(f"- In {os.path.relpath(html, ROOT)} -> {link} (resolved: {os.path.relpath(resolved, ROOT)})")
    return 2

if __name__ == '__main__':
    rc = main()
    sys.exit(rc)
