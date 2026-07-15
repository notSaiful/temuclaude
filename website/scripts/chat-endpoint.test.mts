import assert from 'node:assert/strict';
import test from 'node:test';

import { resolveChatEndpoint } from '../lib/chat-endpoint.ts';

test('uses the same-origin route when no override is configured', () => {
  assert.equal(resolveChatEndpoint(undefined), '/api/chat');
  assert.equal(resolveChatEndpoint('  '), '/api/chat');
  assert.equal(resolveChatEndpoint('/'), '/api/chat');
});

test('adds the chat route to a Cloud Run service base URL', () => {
  assert.equal(
    resolveChatEndpoint('https://temuclaude-chat.example.run.app'),
    'https://temuclaude-chat.example.run.app/api/chat',
  );
  assert.equal(
    resolveChatEndpoint('https://temuclaude-chat.example.run.app/'),
    'https://temuclaude-chat.example.run.app/api/chat',
  );
});

test('keeps full endpoints and intentional proxy paths intact', () => {
  assert.equal(
    resolveChatEndpoint('https://temuclaude-chat.example.run.app/api/chat'),
    'https://temuclaude-chat.example.run.app/api/chat',
  );
  assert.equal(resolveChatEndpoint('/internal/chat'), '/internal/chat');
});
