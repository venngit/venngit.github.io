import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
JSON_PATH = os.path.join(ROOT, 'posts', 'blog-posts.json')

missing = []
checked = 0

if not os.path.exists(JSON_PATH):
    print(f"Error: {JSON_PATH} not found")
    raise SystemExit(1)

with open(JSON_PATH, 'r', encoding='utf-8') as f:
    data = json.load(f)

posts = data.get('posts') or []
for p in posts:
    title = p.get('title') or '<no-title>'
    for key in ('image', 'thumb', 'hero'):
        val = p.get(key)
        if not val:
            continue
        checked += 1
        # Normalize relative paths that may start with ../ or ./
        path = val.replace('\\', '/')
        if path.startswith('../') or path.startswith('./'):
            path = path.split('/', 1)[1]
        # If still absolute (starts with /), remove leading /
        if path.startswith('/'):
            path = path[1:]
        abs_path = os.path.join(ROOT, path)
        if not os.path.exists(abs_path):
            missing.append((title, key, val, abs_path))

print(f"Checked {checked} referenced image paths in {len(posts)} posts.")
if not missing:
    print("All referenced image files exist on disk.")
else:
    print(f"Missing {len(missing)} file(s):")
    for title, key, val, abs_path in missing:
        print(f"- Post: {title!r} field: {key} -> {val} (resolved: {abs_path})")

# Exit code non-zero if missing files
if missing:
    raise SystemExit(2)
else:
    raise SystemExit(0)
