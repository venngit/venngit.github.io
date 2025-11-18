#!/usr/bin/env python3
"""
Scan and repair post HTML files in `posts/`:
- Ensure a single closing </body></html> at the end
- Ensure `/scripts/post-meta.js` and `/scripts/highlight-footer.js` are included once before </body>
- Remove stray text after closing html
"""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
POSTS = ROOT / 'posts'

def repair_text(text):
    orig = text
    # Remove any accidental text after closing </html>
    if '</html>' in text:
        parts = text.split('</html>')
        text = '</html>'.join(parts[:1]) + '</html>'

    # Normalize closing tags: ensure single </body></html>
    # Remove duplicated closing tags
    text = re.sub(r'(</body>\s*){2,}', '</body>\n', text, flags=re.I)
    text = re.sub(r'(</html>\s*){2,}', '</html>\n', text, flags=re.I)

    # Ensure scripts are inside body: remove any scripts after </html> already handled

    # Ensure post-meta.js and highlight-footer.js appear once before </body>
    # Remove any existing occurrences
    text = re.sub(r"<script\s+src=\"/scripts/post-meta.js\"></script>\s*", '', text)
    text = re.sub(r"<script\s+src=\"/scripts/highlight-footer.js\"></script>\s*", '', text)

    # Insert both scripts before closing </body>
    if '</body>' in text:
        text = text.replace('</body>', '    <script src="/scripts/post-meta.js"></script>\n    <script src="/scripts/highlight-footer.js"></script>\n</body>')
    else:
        # If no body tag, append scripts at end
        text = text + '\n    <script src="/scripts/post-meta.js"></script>\n    <script src="/scripts/highlight-footer.js"></script>\n'

    # Clean up common broken fragments like stray ".catch(..." that may have been injected
    text = re.sub(r"\.catch\([^\)]*\);?\s*", '', text)

    changed = (text != orig)
    return text, changed

def main():
    changed_files = []
    for p in sorted(POSTS.glob('*.html')):
        text = p.read_text(encoding='utf-8')
        new_text, changed = repair_text(text)
        if changed:
            p.write_text(new_text, encoding='utf-8')
            changed_files.append(p.name)
            print('Repaired', p.name)
    if changed_files:
        print('\nFiles repaired:', len(changed_files))
    else:
        print('No repairs needed')

if __name__ == '__main__':
    main()
