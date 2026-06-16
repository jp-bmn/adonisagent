const Anthropic = require('@anthropic-ai/sdk');

const client = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY });

const MODELS = {
  default: 'claude-sonnet-4-6',
  fallback: 'claude-opus-4-7',
};

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
  "suggestedUrl": "https://linkedin.com/in/..." or null,
  "reasoning": "One sentence: what you found and why"
}

Rules:
- "verified" = current URL matches this exact person at this org
- "conflict" = you found a better or different URL
- "failed" = not enough signal to verify
- Never return a guessed URL — only URLs from actual search results
- If the person has left the org, set status to "conflict" and note the change in reasoning`;
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

  // Extract JSON from response
  const jsonMatch = textBlocks.match(/\{[\s\S]*\}/);
  if (!jsonMatch) throw new Error('No JSON found in response');

  const result = JSON.parse(jsonMatch[0]);
  return { ...result, model };
}

async function verifyWithFallback(contact) {
  try {
    const result = await verifyContact(contact, MODELS.default);
    // If Sonnet failed, retry with Opus
    if (result.status === 'failed') {
      try {
        const opusResult = await verifyContact(contact, MODELS.fallback);
        return opusResult;
      } catch {
        return result; // return Sonnet's failed result if Opus also fails
      }
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

module.exports = { verifyWithFallback };
