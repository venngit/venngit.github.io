const express = require('express');
const bcrypt = require('bcrypt');
const jwt = require('jsonwebtoken');
const db = require('../lib/db');
const { SECRET } = require('../lib/auth-mw');

const router = express.Router();

// Signup — use once or protect in production
router.post('/signup', async (req, res) => {
  try {
    const { username, password } = req.body;
    if (!username || !password) return res.status(400).json({ error: 'username/password required' });
    const existing = await db.get('SELECT id FROM users WHERE username = ?', [username]);
    if (existing) return res.status(409).json({ error: 'user exists' });
    const hash = await bcrypt.hash(password, 10);
    await db.run('INSERT INTO users(username, password_hash) VALUES(?, ?)', [username, hash]);
    res.json({ ok: true });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

// Login -> returns JWT
router.post('/login', async (req, res) => {
  try {
    const { username, password } = req.body;
    const row = await db.get('SELECT * FROM users WHERE username = ?', [username]);
    if (!row) return res.status(401).json({ error: 'invalid credentials' });
    const match = await bcrypt.compare(password, row.password_hash);
    if (!match) return res.status(401).json({ error: 'invalid credentials' });
    const token = jwt.sign({ uid: row.id, username: row.username }, SECRET, { expiresIn: '12h' });
    res.json({ token });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

module.exports = router;
