const Anthropic = require('@anthropic-ai/sdk');

const client = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY });

const MODELS = {
  default: 'claude-sonnet-4-6',
  fallback: 'claude-opus-4-7',
};

// Detect AI error messages saved as contact names
const ERROR_PATTERNS = [
  /^the provided snippets/i,
  /^unknown$/i,
  /^i (could not|cannot|don't|do not)/i,
  /^no information/i,
  /^based on the (provided|given)/i,
];

function isInvalidName(name) {
  if (!name || name.trim().length < 2) return true;
  return ERROR_PATTERNS.some((p) => p.test(name.trim()));
}

// Only accept real LinkedIn profile URLs — never posts, jobs, or company pages
function isValidProfileUrl(url) {
  if (!url) return false;
  return /^https?:\/\/(www\.)?linkedin\.com\/in\/[a-zA-Z0-9\-_%]+\/?$/.test(url);
}

function buildPrompt(contact) {
  return `You are a data verification assistant. Find the correct LinkedIn profile URL for this hospital executive.

Contact:
- Name: ${contact.name}
- Role: ${contact.role}
- Organization: ${contact.hospital}
- Current URL in our system: ${contact.currentUrl || 'none'}

Search Google for their LinkedIn profile. Then return ONLY valid JSON (no markdown, no backticks):
{
  "status": "verified" | "conflict" | "failed",
  "suggestedUrl": "https://www.linkedin.com/in/..." or null,
  "reasoning": "One sentence: what you found and why"
}

Rules:
- "verified" = current URL is a linkedin.com/in/ profile URL that matches this exact person at this org
- "conflict" = you found a better or different linkedin.com/in/ profile URL
- "failed" = not enough signal to verify
- ONLY return linkedin.com/in/ profile URLs — never linkedin.com/posts/, linkedin.com/jobs/, or company pages
- Never return a guessed URL — only URLs from actual search results
- If the person has left the org, set status to "conflict" and note the change in reasoning
- If the current URL is a post URL (linkedin.com/posts/), always set status to "conflict" and find the real profile`;
}

async function verifyContact(contact, model = MODELS.default) {
  const response = await client.messages.create({
    model,
    max_tokens: 1000,
    tools: [{ type: 'web_search_20250305', name: 'web_search' }],
    messages: [{ role: 'user', content: buildPrompt(contact) }],
  });

  const textBlocks = response.content
    .filter((b) => b.type === 'text')
    .map((b) => b.text)
    .join('\n');

  const jsonMatch = textBlocks.match(/\{[\s\S]*?\}/);
  if (!jsonMatch) throw new Error('No JSON found in response');

  const result = JSON.parse(jsonMatch[0]);

  // Reject any non-profile URLs the model returns
  if (result.suggestedUrl && !isValidProfileUrl(result.suggestedUrl)) {
    result.suggestedUrl = null;
    result.status = 'failed';
    result.reasoning = `Found a URL but it was not a linkedin.com/in/ profile link — ${result.reasoning}`;
  }

  return { ...result, model };
}

async function verifyWithFallback(contact) {
  // Flag contacts with invalid names immediately — don't waste API calls
  if (isInvalidName(contact.name)) {
    return {
      status: 'invalid_name',
      suggestedUrl: null,
      reasoning:
        'Contact name appears to be an AI error message or is missing — pipeline needs to fix this contact.',
      model: null,
    };
  }

  // Flag post URLs immediately before verification
  const hasPostUrl = contact.currentUrl && contact.currentUrl.includes('/posts/');

  try {
    const result = await verifyContact(contact, MODELS.default);
    if (result.status === 'failed') {
      try {
        const opusResult = await verifyContact(contact, MODELS.fallback);
        return opusResult;
      } catch {
        return result;
      }
    }
    // If current URL was a post URL and we got verified, force conflict so it gets updated
    if (hasPostUrl && result.status === 'verified') {
      result.status = 'conflict';
      result.reasoning = `Current URL is a post link, not a profile — ${result.reasoning}`;
    }
    return result;
  } catch (err) {
    return {
      status: 'failed',
      suggestedUrl: null,
      reasoning: `Verification error: ${err.message}`,
      model: MODELS.default,
    };
  }
}

module.exports = { verifyWithFallback, isInvalidName, isValidProfileUrl };
