require('dotenv').config();
const express = require('express');
const cors = require('cors');
const { verifyWithFallback } = require('./verifier');

const app = express();
app.use(cors());
app.use(express.json());

const PORT = process.env.PORT || 3001;
const DELAY_MS = 500;

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

app.get('/health', (_req, res) => {
  res.json({ status: 'ok', service: 'linkedin-verifier' });
});

app.post('/verify', async (req, res) => {
  const { contacts } = req.body;

  if (!Array.isArray(contacts) || contacts.length === 0) {
    return res.status(400).json({ error: 'contacts must be a non-empty array' });
  }

  if (!process.env.ANTHROPIC_API_KEY) {
    return res.status(500).json({ error: 'ANTHROPIC_API_KEY not configured' });
  }

  const promises = contacts.map(async (contact, index) => {
    // Stagger start times to avoid hitting Anthropic API limits all at the exact same millisecond
    await sleep(index * 1500);
    const result = await verifyWithFallback(contact);
    return {
      id: contact.id,
      name: contact.name,
      hospital: contact.hospital,
      currentUrl: contact.currentUrl || null,
      ...result,
    };
  });

  const results = await Promise.all(promises);

  const summary = {
    total: results.length,
    verified: results.filter((r) => r.status === 'verified').length,
    conflicts: results.filter((r) => r.status === 'conflict').length,
    failed: results.filter((r) => r.status === 'failed').length,
    invalid_names: results.filter((r) => r.status === 'invalid_name').length,
  };

  return res.json({ results, summary });
});

app.listen(PORT, () => {
  console.log(`LinkedIn verifier running on port ${PORT}`);
});
