#!/usr/bin/env python3
"""
Normalize filenames in blog-images/ to slug format (lowercase, hyphens, no spaces)
and update references in posts/blog-posts.json and all files in the repo.

Usage:
  python tools/normalize_filenames.py --apply

Without --apply it will run in dry-run mode and print planned changes.

It writes tools/rename-map.json with mapping of old -> new.
"""
import os
import re
import json
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BLOG_IMAGES = ROOT / 'blog-images'
POSTS_JSON = ROOT / 'posts' / 'blog-posts.json'
RENAME_MAP = ROOT / 'tools' / 'rename-map.json'


def slugify(name: str) -> str:
    # Split extension
    name = name.strip()
    if '.' in name:
        base, ext = name.rsplit('.', 1)
        ext = ext.lower()
    else:
        base, ext = name, ''
    # Replace spaces and underscores with hyphens
    base = base.strip()
    base = re.sub(r"[\s_]+", '-', base)
    # Remove characters that are not alnum, hyphen
    base = re.sub(r"[^a-zA-Z0-9\-]", '', base)
    # collapse multiple hyphens
    base = re.sub(r"-+", '-', base)
    base = base.strip('-')
    base = base.lower()
    return f"{base}.{ext}" if ext else base


def find_all_files(root: Path):
    for p in root.rglob('*'):
        if p.is_file():
            yield p


def main(dry_run=True):
    if not BLOG_IMAGES.exists():
        print('No blog-images directory found at', BLOG_IMAGES)
        return

    # Build rename map
    rename_map = {}
    conflicts = {}
    for p in BLOG_IMAGES.iterdir():
        if p.is_file():
            new_name = slugify(p.name)
            if new_name != p.name:
                # Resolve collisions
                candidate = new_name
                i = 1
                while (BLOG_IMAGES / candidate).exists() and (BLOG_IMAGES / candidate).name != p.name:
                    # If the candidate exists and it's not the same file
                    candidate_base = candidate.rsplit('.', 1)[0]
                    ext = candidate.rsplit('.', 1)[1]
                    candidate = f"{candidate_base}-{i}.{ext}"
                    i += 1
                rename_map[p.name] = candidate

    if not rename_map:
        print('No filenames to normalize.')
        return

    print('Planned renames:')
    for old, new in rename_map.items():
        print(f"  {old} -> {new}")

    if dry_run:
        print('\nDry run mode, no files changed. Run with --apply to perform the renames.')
        return

    # Apply renames in filesystem
    applied_map = {}
    for old, new in rename_map.items():
        src = BLOG_IMAGES / old
        dst = BLOG_IMAGES / new
        try:
            src.rename(dst)
            applied_map[old] = new
            print(f"Renamed: {old} -> {new}")
        except Exception as e:
            print(f"Failed to rename {old} -> {new}: {e}")

    # Update posts/blog-posts.json
    if POSTS_JSON.exists():
        try:
            data = json.loads(POSTS_JSON.read_text(encoding='utf-8'))
            changed = False
            for post in data.get('posts', []):
                img = post.get('image')
                if img and isinstance(img, str) and '../blog-images/' in img:
                    fname = img.split('../blog-images/')[-1]
                    if fname in applied_map:
                        newfname = applied_map[fname]
                        post['image'] = img.replace(fname, newfname)
                        changed = True
                        print(f"Updated JSON image reference: {fname} -> {newfname}")
            if changed:
                POSTS_JSON.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding='utf-8')
                print('Updated', POSTS_JSON)
        except Exception as e:
            print('Failed to update', POSTS_JSON, e)

    # Update references across repo files
    all_files = list(find_all_files(ROOT))
    refs_changed = 0
    for f in all_files:
        # Only text files
        try:
            text = f.read_text(encoding='utf-8')
        except Exception:
            continue
        updated = text
        for old, new in applied_map.items():
            if old in updated:
                updated = updated.replace(old, new)
        if updated != text:
            f.write_text(updated, encoding='utf-8')
            refs_changed += 1
            print(f'Updated references in {f.relative_to(ROOT)}')

    # Write rename map
    RENAME_MAP.write_text(json.dumps(applied_map, indent=2), encoding='utf-8')
    print('\nDone. Files renamed:', len(applied_map), 'files. Files updated:', refs_changed)
    print('Rename mapping written to', RENAME_MAP)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--apply', action='store_true', help='Perform the renames (otherwise dry-run)')
    args = parser.parse_args()
    main(dry_run=not args.apply)
