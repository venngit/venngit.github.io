"""CI / preflight validator for the site.

Checks performed:
- posts/blog-posts.json is valid JSON with a top-level 'posts' list
- For each post, checks required fields exist (title, published, image)
- Any referenced local image files (image, thumb, hero) exist on disk
- Warns about filenames containing spaces or uppercase letters
- Optionally checks image size (KB) and dimensions (max width/height)

Exit codes:
- 0: all checks passed (or only warnings if warn-only)
- 1: validation / JSON parse error
- 2: missing files or violations found (fatal unless --warn-only)

Usage:
  python tools/ci_validate.py [--json posts/blog-posts.json] [--max-kb 500] [--max-width 4000] [--max-height 4000] [--warn-only]

Designed to run in CI (install Pillow before running if dimension checks are enabled).
"""
import argparse
import json
import os
import sys
from pathlib import Path

try:
    from PIL import Image
    PIL_AVAILABLE = True
except Exception:
    PIL_AVAILABLE = False

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_JSON = ROOT / 'posts' / 'blog-posts.json'


def load_json(path):
    try:
        with open(path, 'r', encoding='utf-8') as fh:
            data = json.load(fh)
        return data
    except Exception as e:
        print(f"ERROR: Failed to load JSON {path}: {e}")
        return None


def is_local(link: str):
    if not link:
        return False
    l = link.strip()
    if l.startswith(('http://', 'https://', '//', 'data:', 'mailto:', 'tel:')):
        return False
    return True


def resolve_path(ref: str) -> Path:
    # normalize ./ ../ and leading /
    ref = ref.replace('\\', '/')
    if ref.startswith('../') or ref.startswith('./'):
        ref = ref.split('/', 1)[1]
    if ref.startswith('/'):
        ref = ref.lstrip('/')
    return (ROOT / ref)


def check_posts(data, args):
    problems = []
    warnings = []

    posts = data.get('posts')
    if posts is None:
        problems.append("JSON does not contain top-level 'posts' array")
        return problems, warnings

    for p in posts:
        title = p.get('title', '<no-title>')
        # required fields
        if not p.get('image'):
            problems.append(f"Post '{title}': missing 'image' field")
            continue
        for key in ('image', 'thumb', 'hero'):
            v = p.get(key)
            if not v:
                continue
            if not is_local(v):
                # external — skip existence checks
                continue
            path = resolve_path(v)
            if not path.exists():
                problems.append(f"Post '{title}': referenced file for '{key}' not found -> {v} (resolved: {path})")
            else:
                # filename warnings
                fname = path.name
                if ' ' in fname:
                    warnings.append(f"Post '{title}': filename contains spaces -> {fname}")
                if any(c.isupper() for c in fname):
                    warnings.append(f"Post '{title}': filename contains uppercase letters -> {fname}")
                # size/dimension checks
                if args.max_kb is not None:
                    try:
                        kb = path.stat().st_size / 1024
                        if kb > args.max_kb:
                            warnings.append(f"Post '{title}': file {fname} is {kb:.1f}KB > max_kb {args.max_kb}")
                    except Exception as e:
                        warnings.append(f"Could not determine size for {path}: {e}")
                if (args.max_width or args.max_height) and PIL_AVAILABLE:
                    try:
                        with Image.open(path) as im:
                            w, h = im.size
                            if args.max_width and w > args.max_width:
                                warnings.append(f"Post '{title}': image {fname} width {w}px > max_width {args.max_width}")
                            if args.max_height and h > args.max_height:
                                warnings.append(f"Post '{title}': image {fname} height {h}px > max_height {args.max_height}")
                    except Exception as e:
                        warnings.append(f"Could not open image {path} for dimension check: {e}")
                elif (args.max_width or args.max_height) and not PIL_AVAILABLE:
                    warnings.append("Pillow not installed — skipping image dimension checks (install pillow to enable)")

    return problems, warnings


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument('--json', default=str(DEFAULT_JSON), help='Path to posts/blog-posts.json')
    parser.add_argument('--max-kb', type=float, default=1024, help='Warn if image file size exceeds this KB value (default: 1024KB)')
    parser.add_argument('--max-width', type=int, default=4000, help='Warn if image width exceeds this (px)')
    parser.add_argument('--max-height', type=int, default=4000, help='Warn if image height exceeds this (px)')
    parser.add_argument('--warn-only', action='store_true', help='Do not exit non-zero on problems; only print')
    parser.add_argument('--fail-on-warn', action='store_true', help='Treat warnings as failures and exit non-zero')

    args = parser.parse_args(argv)

    data = load_json(args.json)
    if data is None:
        return 1

    problems, warnings = check_posts(data, args)

    if warnings:
        print("Warnings:")
        for w in warnings:
            print("  - ", w)
    else:
        print("No warnings.")

    # If there are no fatal problems but warnings exist and fail_on_warn is set, treat as fatal
    if problems:
        print('\nProblems:')
        for p in problems:
            print('  - ', p)
        if args.warn_only:
            return 0
        return 2
    if warnings and args.fail_on_warn:
        print('\nFailing because --fail-on-warn was provided and warnings were emitted.')
        return 2

    print('\nAll checks passed.')
    return 0


if __name__ == '__main__':
    rc = main(sys.argv[1:])
    sys.exit(rc)
