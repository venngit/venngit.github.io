const db = require('../lib/db');

async function migrate() {
  try {
    await db.run(`CREATE TABLE IF NOT EXISTS users (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      username TEXT UNIQUE NOT NULL,
      password_hash TEXT NOT NULL
    );`);
    await db.run(`CREATE TABLE IF NOT EXISTS posts (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      title TEXT NOT NULL,
      slug TEXT UNIQUE NOT NULL,
      excerpt TEXT,
      body TEXT NOT NULL,
      images_json TEXT,
      published INTEGER DEFAULT 0,
      created_at TEXT NOT NULL,
      updated_at TEXT
    );`);
    await db.run(`CREATE TABLE IF NOT EXISTS images (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      filename TEXT,
      url TEXT,
      created_at TEXT
    );`);
    console.log('Migration finished. DB path:', db.DB_PATH);
  } catch (e) {
    console.error('Migration failed:', e);
  } finally {
    process.exit(0);
  }
}

migrate();
