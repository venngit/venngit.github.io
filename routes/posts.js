const express = require('express');
const db = require('../lib/db');
const { requireAuth } = require('../lib/auth-mw');

const router = express.Router();

// list published posts (public)
router.get('/', async (req, res) => {
  try {
    const rows = await db.all('SELECT id, title, slug, excerpt, body, images_json, published, created_at FROM posts WHERE published=1 ORDER BY created_at DESC');
    const posts = rows.map(r => ({ ...r, images: r.images_json ? JSON.parse(r.images_json) : [] }));
    res.json(posts);
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

// admin: create post
router.post('/', requireAuth, async (req, res) => {
  try {
    const { title, slug, excerpt, body, images = [], published = false } = req.body;
    if (!title || !slug || !body) return res.status(400).json({ error: 'title/slug/body required' });
    const created_at = new Date().toISOString();
    const images_json = JSON.stringify(images);
    const info = await db.run('INSERT INTO posts(title, slug, excerpt, body, images_json, published, created_at) VALUES(?,?,?,?,?,?,?)',
      [title, slug, excerpt || '', body, images_json, published ? 1 : 0, created_at]);
    res.json({ id: info.lastID });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

module.exports = router;
