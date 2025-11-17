const express = require('express');
const fs = require('fs');
const path = require('path');
const cors = require('cors');

const app = express();
const PORT = process.env.PORT || 3000;
const DATA_FILE = path.join(__dirname, 'awards.json');

let awards = [];
let lastUpdated = null;

// Load awards.json (if missing, start empty)
function loadAwards() {
  try {
    const raw = fs.readFileSync(DATA_FILE, 'utf8');
    awards = JSON.parse(raw);
  } catch (err) {
    console.warn('Could not read awards.json, starting with empty array.');
    awards = [];
  }
}
function saveAwards() {
  try {
    fs.writeFileSync(DATA_FILE, JSON.stringify(awards, null, 2), 'utf8');
  } catch (err) {
    console.error('Failed to write awards.json:', err);
  }
}

// If Node version lacks fetch, a runtime polyfill is required.
// Node 18+ includes fetch. This code will error if fetch is missing.
async function fetchText(url) {
  try {
    const res = await fetch(url, { redirect: 'follow' });
    if (!res.ok) return null;
    return await res.text();
  } catch (e) {
    return null;
  }
}

function extractDateFromText(text) {
  if (!text) return null;
  const months = 'January|February|March|April|May|June|July|August|September|October|November|December';
  const regex1 = new RegExp(`\\b(${months})\\s+\\d{1,2},\\s*\\d{4}\\b`, 'i'); // "January 3, 2025"
  const regex2 = /\b\d{4}-\d{2}-\d{2}\b/; // "2025-01-03"
  const m1 = text.match(regex1);
  if (m1) return m1[0];
  const m2 = text.match(regex2);
  if (m2) {
    const d = new Date(m2[0]);
    if (!isNaN(d)) return d.toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' });
  }
  return null;
}

async function tryUpdateDeadlines() {
  console.log('Running deadline update job...');
  let changed = false;
  for (const award of awards) {
    if (!award.latestOpeningEntry || award.latestOpeningEntry === 'N/A') continue;

    // fetch if not fetched yet or older than 24h
    const fetchedAt = award._fetchedAt ? new Date(award._fetchedAt) : null;
    if (fetchedAt && (Date.now() - fetchedAt.getTime()) < 24 * 60 * 60 * 1000) continue;

    try {
      const html = await fetchText(award.latestOpeningEntry);
      award._fetchedAt = new Date().toISOString();
      if (!html) continue;
      const found = extractDateFromText(html);
      if (found && found !== award.deadline) {
        console.log(`Update ${award.name}: ${award.deadline} -> ${found}`);
        award.deadline = found;
        changed = true;
      }
    } catch (err) {
      // ignore per-award errors
    }
  }
  lastUpdated = new Date().toISOString();
  if (changed) saveAwards();
}

// startup
loadAwards();
tryUpdateDeadlines().catch(err => console.error(err));
// run every 12 hours
setInterval(() => tryUpdateDeadlines().catch(err => console.error(err)), 12 * 60 * 60 * 1000);

// ensure folders exist
const uploadsDir = path.join(__dirname, 'uploads');
const dataDir = path.join(__dirname, 'data');
if (!fs.existsSync(uploadsDir)) fs.mkdirSync(uploadsDir, { recursive: true });
if (!fs.existsSync(dataDir)) fs.mkdirSync(dataDir, { recursive: true });

app.use(cors());
app.use(express.json({ limit: '10mb' }));

// serve uploaded images and static frontend
app.use('/uploads', express.static(uploadsDir));
app.use(express.static(__dirname));

// mount routes
app.use('/api/auth', require('./routes/auth'));
app.use('/api/uploads', require('./routes/uploads'));
app.use('/api/posts', require('./routes/posts'));

// health
app.get('/health', (req, res) => res.json({ ok: true, time: new Date().toISOString() }));

// API endpoint for awards
app.get('/api/awards', (req, res) => {
  res.set('Access-Control-Allow-Origin', '*');
  res.json({ awards, lastUpdated });
});

app.listen(PORT, () => {
  console.log(`Photowards server listening on http://0.0.0.0:${PORT}`);
});

// Initial load and first update
loadAwards();
tryUpdateDeadlines().catch(err => console.error(err));
// Schedule periodic updates (every 12 hours)
setInterval(() => tryUpdateDeadlines().catch(err => console.error(err)), 12 * 60 * 60 * 1000);
