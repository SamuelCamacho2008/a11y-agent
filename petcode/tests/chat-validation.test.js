import assert from 'node:assert/strict';
import test from 'node:test';
import { isSafeChatMessage } from '../src/chat-validation.js';

test('accepts a short message that does not contain contact details', () => {
  assert.equal(isSafeChatMessage('Lo vi cerca del parque central.'), true);
});

test('rejects empty or oversized messages', () => {
  assert.equal(isSafeChatMessage('  '), false);
  assert.equal(isSafeChatMessage('a'.repeat(1001)), false);
});

test('rejects email addresses, phone numbers, and URLs', () => {
  assert.equal(isSafeChatMessage('Escríbeme a persona@example.com'), false);
  assert.equal(isSafeChatMessage('Llámame al +57 300 123 4567'), false);
  assert.equal(isSafeChatMessage('Mira https://example.com'), false);
});
