import test from 'node:test'
import assert from 'node:assert/strict'
import { api } from '../src/api.js'

test('an offline proxy with an empty body gives a clear unconfirmed-save error', async () => {
  const original = globalThis.fetch
  globalThis.fetch = async () => new Response('', { status: 502 })
  try { await assert.rejects(api('/sessions'), /Saving is unconfirmed/) }
  finally { globalThis.fetch = original }
})

test('database failure is preserved rather than treated as a successful save', async () => {
  const original = globalThis.fetch
  globalThis.fetch = async () => new Response(JSON.stringify({ detail: 'Database did not save.' }), { status: 503 })
  try { await assert.rejects(api('/sessions'), /Database did not save/) }
  finally { globalThis.fetch = original }
})
