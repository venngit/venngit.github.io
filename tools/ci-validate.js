#!/usr/bin/env node
const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

let imageSize;
try {
  imageSize = require('image-size');
} catch (e) {
  imageSize = null;
}

const ROOT = path.resolve(__dirname, '..');
const DEFAULT_JSON = path.join(ROOT, 'posts', 'blog-posts.json');

function parseArgs() {
  const args = { json: DEFAULT_JSON, max_kb: 1024, max_width: 4000, max_height: 4000, warn_only: false, fail_on_warn: false };
  const argv = process.argv.slice(2);
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--json' && argv[i+1]) { args.json = argv[++i]; }
    else if (a === '--max-kb' && argv[i+1]) { args.max_kb = parseFloat(argv[++i]); }
    else if (a === '--max-width' && argv[i+1]) { args.max_width = parseInt(argv[++i], 10); }
    else if (a === '--max-height' && argv[i+1]) { args.max_height = parseInt(argv[++i], 10); }
    else if (a === '--warn-only') { args.warn_only = true; }
    else if (a === '--fail-on-warn') { args.fail_on_warn = true; }
  }
  return args;
}

function isLocal(link) {
  if (!link) return false;
  const l = link.trim();
  if (l.startsWith('http://') || l.startsWith('https://') || l.startsWith('//') || l.startsWith('data:') || l.startsWith('mailto:') || l.startsWith('tel:')) return false;
  return true;
}

function resolveRef(ref) {
  let p = ref.replace(/\\/g, '/');
  if (p.startsWith('../') || p.startsWith('./')) p = p.split('/').slice(1).join('/');
  if (p.startsWith('/')) p = p.replace(/^\//, '');
  return path.join(ROOT, p);
}

function loadJson(jsonPath) {
  try {
    const txt = fs.readFileSync(jsonPath, 'utf8');
    return JSON.parse(txt);
  } catch (e) {
    console.error(`ERROR: failed to load JSON ${jsonPath}: ${e}`);
    return null;
  }
}

function run() {
  const args = parseArgs();
  const data = loadJson(args.json);
  if (!data) return 1;
  const posts = data.posts || [];
  const problems = [];
  const warnings = [];

  posts.forEach(p => {
    const title = p.title || '<no-title>';
    if (!p.image) {
      problems.push(`Post '${title}': missing 'image' field`);
      return;
    }
    ['image','thumb','hero'].forEach(key => {
      const v = p[key];
      if (!v) return;
      if (!isLocal(v)) return;
      const resolved = resolveRef(v);
      if (!fs.existsSync(resolved)) {
        problems.push(`Post '${title}': referenced file for '${key}' not found -> ${v} (resolved: ${resolved})`);
        return;
      }
      const fname = path.basename(resolved);
      if (fname.includes(' ')) warnings.push(`Post '${title}': filename contains spaces -> ${fname}`);
      if (/[A-Z]/.test(fname)) warnings.push(`Post '${title}': filename contains uppercase letters -> ${fname}`);
      try {
        const kb = fs.statSync(resolved).size / 1024;
        if (args.max_kb && kb > args.max_kb) warnings.push(`Post '${title}': file ${fname} is ${kb.toFixed(1)}KB > max_kb ${args.max_kb}`);
      } catch (e) {
        warnings.push(`Could not determine size for ${resolved}: ${e}`);
      }
      if ((args.max_width || args.max_height) && imageSize) {
        try {
          const dim = imageSize(resolved);
          const w = dim.width, h = dim.height;
          if (args.max_width && w > args.max_width) warnings.push(`Post '${title}': image ${fname} width ${w}px > max_width ${args.max_width}`);
          if (args.max_height && h > args.max_height) warnings.push(`Post '${title}': image ${fname} height ${h}px > max_height ${args.max_height}`);
        } catch (e) {
          warnings.push(`Could not read dimensions for ${resolved}: ${e}`);
        }
      } else if ((args.max_width || args.max_height) && !imageSize) {
        warnings.push('image-size module not installed — skipping dimension checks');
      }
    });
  });

  if (warnings.length) {
    console.log('Warnings:');
    warnings.forEach(w => console.log('  -', w));
  } else {
    console.log('No warnings.');
  }

  if (problems.length) {
    console.log('\nProblems:');
    problems.forEach(p => console.log('  -', p));
    if (args.warn_only) return 0;
    return 2;
  }

  if (warnings.length && args.fail_on_warn) {
    console.log('\nFailing because --fail-on-warn provided and warnings exist.');
    return 2;
  }

  console.log('\nAll checks passed.');
  return 0;
}

const rc = run();
process.exit(rc);
