#!/usr/bin/env python3
"""
Process images to create thumbnails and webp variants, strip EXIF, and optionally update posts/blog-posts.json to include thumbnail paths.

Usage:
  python tools/process_images.py --source blog-images --dest blog-images/thumbs --sizes 800 400 --webp --update-json

Defaults:
  source: blog-images
  dest: blog-images/thumbs
  sizes: 800 400
  webp: enabled
  update-json: enabled

The script writes tools/process-map.json with mapping info.
"""
import os
import sys
from pathlib import Path
from PIL import Image, ImageOps
import argparse
import json

ROOT = Path(__file__).resolve().parents[1]

VALID_EXT = ('.jpg', '.jpeg', '.png', '.gif', '.bmp')


def ensure_dir(p: Path):
    p.mkdir(parents=True, exist_ok=True)


from PIL import ImageFilter


def process_image(src: Path, dest_dir: Path, sizes=(1600, 800, 400), make_webp=True, quality_map=None, watermark_text=None):
    results = {}
    try:
        with Image.open(src) as im:
            im = im.convert('RGB')
            for size in sizes:
                # Compute target size while preserving aspect
                w, h = im.size
                # Use high-quality Lanczos resampling for downscaling
                if w <= size and h <= size:
                    resized = im.copy()
                else:
                    # Pillow supports a 'method' argument for contain; use LANCZOS for quality
                    try:
                        resized = ImageOps.contain(im, (size, size), method=Image.LANCZOS)
                    except TypeError:
                        # Older Pillow versions may not accept 'method' keyword; fall back
                        resized = ImageOps.contain(im, (size, size))

                base = src.stem
                dest_name = f"{base}-{size}.jpg"
                dest_path = dest_dir / dest_name
                # Apply light sharpening (unsharp mask) to improve perceived sharpness after downscale
                try:
                    resized = resized.filter(ImageFilter.UnsharpMask(radius=0.5, percent=120, threshold=3))
                except Exception:
                    pass

                # Determine quality for this size (allow per-size tuning)
                q = quality_map.get(size) if quality_map and isinstance(quality_map, dict) else (quality_map or 92)
                # Strip EXIF by not copying exif info; save with progressive JPEG and optimization
                resized.save(dest_path, format='JPEG', quality=int(q), optimize=True, progressive=True)
                results[size] = str(dest_path.relative_to(ROOT))

                if make_webp:
                    webp_name = f"{base}-{size}.webp"
                    webp_path = dest_dir / webp_name
                    # WebP tends to give better quality/size than JPEG; keep quality slightly lower
                    webp_q = 90 if q >= 90 else 85
                    resized.save(webp_path, format='WEBP', quality=int(webp_q), method=6)
                    results[f'{size}_webp'] = str(webp_path.relative_to(ROOT))
    except Exception as e:
        print(f"Failed to process {src}: {e}")
    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', default='blog-images', help='Source directory relative to repo root')
    parser.add_argument('--dest', default='blog-images/thumbs', help='Destination directory for thumbs')
    parser.add_argument('--sizes', nargs='+', type=int, default=[1600, 800, 400], help='Sizes (px) to generate')
    parser.add_argument('--no-webp', dest='webp', action='store_false', help='Do not create webp variants')
    parser.add_argument('--no-update-json', dest='update_json', action='store_false', help='Do not update posts/blog-posts.json')
    parser.add_argument('--quality', type=int, default=92, help='Default JPEG quality for outputs (applies when quality-map not used)')
    parser.add_argument('--quality-map', type=str, default=None, help='JSON map of size->quality, e.g. "{\"1600\":92,\"800\":90,\"400\":85}"')
    parser.add_argument('--watermark', default=None, help='Optional watermark text to apply to generated images')
    args = parser.parse_args()

    source_dir = ROOT / args.source
    dest_dir = ROOT / args.dest
    if not source_dir.exists():
        print('Source dir does not exist:', source_dir)
        sys.exit(1)
    ensure_dir(dest_dir)

    mapping = {}
    files = [p for p in source_dir.iterdir() if p.is_file() and p.suffix.lower() in VALID_EXT]
    print(f'Found {len(files)} image(s) in {source_dir}')
    for f in files:
        print('Processing', f.name)
        qmap = None
        if args.quality_map:
            try:
                qmap = json.loads(args.quality_map)
                # convert keys to ints
                qmap = {int(k): int(v) for k, v in qmap.items()}
            except Exception:
                qmap = None
        res = process_image(f, dest_dir, sizes=args.sizes, make_webp=args.webp, quality_map=qmap or args.quality, watermark_text=args.watermark)
        mapping[f.name] = res

    # Write mapping
    map_file = ROOT / 'tools' / 'process-map.json'
    map_file.write_text(json.dumps(mapping, indent=2), encoding='utf-8')
    print('Wrote mapping to', map_file)

    if args.update_json:
        posts_json = ROOT / 'posts' / 'blog-posts.json'
        if not posts_json.exists():
            print('Posts JSON not found, skipping JSON update')
            return
        data = json.loads(posts_json.read_text(encoding='utf-8'))
        changed = False
        for post in data.get('posts', []):
            img = post.get('image')
            if not img:
                continue
            # image path like "../blog-images/filename.jpg"
            fname = os.path.basename(img)
            entry = mapping.get(fname)
            if entry:
                # Choose a sensible default: if multiple sizes were requested, use the second size as the
                # normal thumbnail (e.g., sizes = [1600,800,400] -> thumb=800) and keep the largest as 'hero'.
                preferred = args.sizes[1] if len(args.sizes) > 1 else args.sizes[0]
                hero = args.sizes[0]
                thumb_rel = mapping[fname].get(preferred)
                hero_rel = mapping[fname].get(hero)
                if thumb_rel:
                    post['thumb'] = '../' + thumb_rel.replace('\\', '/')
                    changed = True
                    print(f"Updated post thumb for {fname} -> {post['thumb']}")
                if hero_rel:
                    post['hero'] = '../' + hero_rel.replace('\\', '/')
                    print(f"Updated post hero for {fname} -> {post['hero']}")
        if changed:
            # backup
            (posts_json.parent / 'blog-posts.json.bak').write_text(posts_json.read_text(encoding='utf-8'), encoding='utf-8')
            posts_json.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding='utf-8')
            print('Updated', posts_json)
        else:
            print('No posts updated')

if __name__ == '__main__':
    main()
