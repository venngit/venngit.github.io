git pull
import json
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
posts_json = ROOT / 'posts' / 'blog-posts.json'
if not posts_json.exists():
    print('posts/blog-posts.json not found')
    raise SystemExit(1)

data = json.loads(posts_json.read_text(encoding='utf-8'))
processed = []
skipped = []

for post in data.get('posts', []):
    img = post.get('image')
    if not img:
        skipped.append((post.get('title'), None, 'no image'))
        continue
    fname = os.path.basename(img)
    # Candidate sources in order of preference
    candidates = [ROOT / 'tools' / '_water_tmp' / fname, ROOT / 'raw-images' / fname, ROOT / 'blog-images' / fname]
    source = None
    for c in candidates:
        if c.exists():
            source = c
            break
    if source is None:
        skipped.append((post.get('title'), fname, 'no source found'))
        continue
    # Determine source dir relative to ROOT
    source_dir = os.path.relpath(source.parent, ROOT)
    print(f'Using source {source_dir} for {fname}')
    cmd = ['python', str(ROOT / 'tools' / 'process_images.py'), '--source', source_dir, '--dest', 'blog-images/thumbs', '--file', fname, '--no-update-json']
    try:
        subprocess.check_call(cmd)
        processed.append((post.get('title'), fname, source_dir))
    except subprocess.CalledProcessError as e:
        skipped.append((post.get('title'), fname, f'process failed: {e}'))

print('\nProcessed:')
for p in processed:
    print(' -', p)
print('\nSkipped:')
for s in skipped:
    print(' -', s)

# After processing, stage the thumbnails
subprocess.call(['git', 'add', 'blog-images/thumbs'])

if processed:
    commit_msg = 'Regenerate all thumbnails from originals (remove watermark)'
    subprocess.call(['git', 'commit', '-m', commit_msg])
    print('Committed thumbnails')
else:
    print('No thumbnails processed; nothing committed')
