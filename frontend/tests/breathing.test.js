import test from 'node:test'
import assert from 'node:assert/strict'
import { DURATION, Pacer, phaseAt } from '../src/breathing.js'

test('inhale/exhale boundaries preserve four and six counts', () => {
  assert.equal(phaseAt(0).phase, 'Breathe in')
  assert.equal(phaseAt(3.99).count, 4)
  assert.equal(phaseAt(4).phase, 'Breathe out')
  assert.equal(phaseAt(4).count, 1)
  assert.equal(phaseAt(9.99).count, 6)
  assert.equal(phaseAt(10).cycle, 2)
  assert.equal(phaseAt(59.9).cycle, 6)
  assert.equal(DURATION, 60)
})

test('timing uses elapsed clock time, not number of callbacks', () => {
  let clock = 0
  const p = new Pacer(() => clock)
  p.start()
  for (clock = 400; clock <= 59600; clock += 400) p.tick()
  clock = 60080
  assert.equal(p.tick().complete, true)
  assert.equal(p.elapsed(), 60.08)
})

test('a voluntary pause is excluded and does not accumulate on resume', () => {
  let clock = 0
  const p = new Pacer(() => clock)
  p.start()
  clock = 1100
  p.pause()
  clock = 31100
  assert.equal(p.elapsed(), 1.1)
  p.resume()
  clock = 32100
  assert.equal(p.elapsed(), 2.1)
})

test('long blocked/background gap is an interruption, not successful guidance', () => {
  let clock = 0
  const p = new Pacer(() => clock)
  p.start()
  clock = 65000
  assert.equal(p.tick().interrupted, true)
})

test('restart discards old accumulated time', () => {
  let clock = 0
  const p = new Pacer(() => clock)
  p.start()
  clock = 4000
  p.pause()
  p.start()
  assert.equal(p.elapsed(), 0)
})
