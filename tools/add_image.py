#!/usr/bin/env python3
"""
Add a new blog image and post.

This script implements the flow:
 1. take a source image (pasted into `blog-images` or provided path)
 2. normalize/slugify the filename (avoid numeric suffixes where possible)
 3. watermark the original into `blog-images/<name>` using `tools/watermark.py`
 4. add a post entry to `posts/blog-posts.json` with today's published date
 5. run `tools/process_images.py --file <name>` to create thumbnails and update JSON

Usage examples:
  python tools/add_image.py --src blog-images/new-photo.jpg
  python tools/add_image.py --src raw-images/IMG_1234.JPG --title "My Walk"

The script is conservative: it will not overwrite an existing post with the same slug unless --force is passed.
"""
import argparse
import json
import os
import re
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def slugify(name: str) -> str:
    # lower, remove extension, replace spaces with hyphens, strip trailing numbers
    base = Path(name).stem
    # replace underscores and spaces
    s = re.sub(r'[\s_]+', '-', base)
    # remove trailing hyphen + digits (e.g. -1, -2) to avoid numbered titles
    s = re.sub(r'-\d+$', '', s)
    # remove anything that's not alnum or hyphen
    s = re.sub(r'[^a-zA-Z0-9\-]', '', s)
    return s.lower()


def load_posts():
    p = ROOT / 'posts' / 'blog-posts.json'
    data = json.loads(p.read_text(encoding='utf-8'))
    return data, p


def save_posts(data, path: Path):
    # backup
    bak = path.parent / (path.name + '.bak')
    bak.write_text(path.read_text(encoding='utf-8'), encoding='utf-8')
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding='utf-8')


def find_conflict(slug: str, posts: list) -> bool:
    for p in posts:
        img = p.get('image')
        if not img:
            continue
        fname = os.path.basename(img)
        if Path(fname).stem == slug:
            return True
    return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--src', required=True, help='Source image path (relative to repo root)')
    parser.add_argument('--title', default=None, help='Optional title for the post (defaults to slugified filename)')
    parser.add_argument('--watermark-text', default='monoismore.com', help='Watermark text to apply')
    parser.add_argument('--watermark-size', type=int, default=32, help='Watermark font size')
    parser.add_argument('--force', action='store_true', help='Overwrite existing post/image if slug conflicts')
    args = parser.parse_args()

    src_path = (ROOT / args.src).resolve()
    if not src_path.exists():
        print('Source image not found:', src_path)
        raise SystemExit(1)

    slug = slugify(src_path.name)
    if not slug:
        print('Could not generate slug from filename')
        raise SystemExit(1)

    # Determine dest filename and ensure extension is .jpg
    dest_name = f"{slug}.jpg"
    dest_path = ROOT / 'blog-images' / dest_name

    posts_data, posts_path = load_posts()
    if find_conflict(slug, posts_data.get('posts', [])) and not args.force:
        print(f'A post or image with slug "{slug}" already exists. Use --force to overwrite.')
        raise SystemExit(1)

    # Copy source to a temp folder to apply watermark and to preserve original if needed
    tmp_dir = ROOT / 'tools' / '_addimg_tmp'
    if tmp_dir.exists():
        shutil.rmtree(tmp_dir)
    tmp_dir.mkdir(parents=True)
    tmp_src = tmp_dir / src_path.name
    shutil.copy2(src_path, tmp_src)

    # Apply watermark to the file in-place into blog-images via tools/watermark.py
    # watermark.py expects source folder and dest folder; we'll put a single file in tmp and dest to blog-images
    print('Watermarking and copying to', dest_path)
    cmd = [
        'python', str(ROOT / 'tools' / 'watermark.py'),
        '--source', str(tmp_dir),
        '--dest', str(ROOT / 'blog-images'),
        '--text', args.watermark_text,
        '--size', str(args.watermark_size)
    ]
    subprocess.check_call(cmd)

    # Ensure the watermarked file exists
    if not dest_path.exists():
        print('Expected watermarked image not found at', dest_path)
        raise SystemExit(1)

    # Add post entry to posts/blog-posts.json
    title = args.title or slug.replace('-', ' ').title()
    today = datetime.now().strftime('%d-%m-%Y')
    new_post = {
        'title': title,
        'published': today,
        'image': f"../blog-images/{dest_name}",
        'link': f"posts/{slug}.html",
        'hasMap': False,
        'thumb': f"../blog-images/thumbs/{slug}-800.jpg",
        'hero': f"../blog-images/thumbs/{slug}-1600.jpg"
    }

    # Append and save
    posts = posts_data.get('posts', [])
    posts.insert(0, new_post)
    posts_data['posts'] = posts
    save_posts(posts_data, posts_path)
    print('Added post to', posts_path)

    # Create post page from template (no-map template)
    tmpl = ROOT / 'posts' / 'post-template.html'
    if tmpl.exists():
        tpl_text = tmpl.read_text(encoding='utf-8')
        page_path = ROOT / 'posts' / f"{slug}.html"
        # Minimal replacement: set <title> and the image src in template if placeholders exist
        tpl_text = tpl_text.replace('{{TITLE}}', title)
        tpl_text = tpl_text.replace('{{IMAGE}}', f"../blog-images/{dest_name}")
        page_path.write_text(tpl_text, encoding='utf-8')
        print('Created post page', page_path)
    else:
        print('Template not found; create a post manually at posts/%s.html' % slug)

    # Run process_images to generate thumbs and update posts JSON
    print('Generating thumbnails and updating JSON')
    proc_cmd = ['python', str(ROOT / 'tools' / 'process_images.py'), '--file', dest_name]
    subprocess.check_call(proc_cmd)

    # Stage changes and provide next steps
    subprocess.check_call(['git', 'add', 'blog-images', 'blog-images/thumbs', 'posts/blog-posts.json', f'posts/{slug}.html'])
    print('\nDone. Staged new image, thumbs, post JSON and post HTML. Commit them with an appropriate message.')


if __name__ == '__main__':
    main()
