<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { api } from './api'
import { DURATION, Pacer, phaseAt } from './breathing'
import { support } from './content'
import './style.css'

const page = ref('practice')
const health = ref(null)
const apiError = ref('')
const notice = ref('')
const sessions = ref([])
const conversations = ref([])
const historyLoading = ref(false)
const cue = ref('circle')
const remember = ref(false)
const preferenceStatus = ref('')
const preferenceBusy = ref(false)
const reducedMotion = ref(false)
const current = ref(null)
const seconds = ref(0)
const paused = ref(false)
const busy = ref(false)
const initializing = ref(true)
const ending = ref(false)
const outcome = ref(null)
const setupSeconds = ref(null)
let entryDisplayedAt = performance.now()
const pendingEvent = ref(null)
const pendingStart = ref(null)
const saveError = ref('')
const supportDialog = ref(null)
const title = ref(null)
const pacer = new Pacer()
let interval = null
let media
let startRequestId = null
const view = computed(() => phaseAt(seconds.value))
const exerciseOpen = computed(() => current.value && ['active', 'paused'].includes(current.value.status))
const isMock = computed(() => health.value?.model_mode === 'mock')
const cueVisible = computed(() => cue.value === 'circle' && !reducedMotion.value)
const conversationId = ref(localStorage.getItem('breathing-conversation') || '')
const messages = ref([])
const question = ref('')
const askBusy = ref(false)
const askError = ref('')
const simulateFailure = ref(false)
const lastRequest = ref(null)
const retrieval = ref(null)
const requestRecoverable = ref(false)
const newConversationRequest = ref(crypto.randomUUID())
watch(() => page.value === 'practice' && !exerciseOpen.value && !outcome.value,
  (showingEntry) => { if (showingEntry) entryDisplayedAt = performance.now() }, { immediate: true })

function timestamp(value) { return new Date(value).toLocaleString([], { dateStyle: 'medium', timeStyle: 'short' }) }
function duration(value) { return `${Number(value).toFixed(1)} s` }
async function focusTitle() { await nextTick(); title.value?.focus() }
function stopTicks() { clearInterval(interval); interval = null }
function beginTicks(resume = false) {
  if (resume) pacer.resume()
  else {
    setupSeconds.value = (performance.now() - entryDisplayedAt) / 1000
    pacer.start()
  }
  stopTicks()
  interval = setInterval(() => {
    if (paused.value || ending.value) return
    const state = pacer.tick()
    seconds.value = state.seconds
    if (state.interrupted) {
      notice.value = 'The pacing was interrupted. This session will be marked stopped; you can start again.'
      finish('stop', 'timing_interruption')
    } else if (state.complete) finish('complete')
  }, 80)
}

async function loadHistory() {
  historyLoading.value = true
  apiError.value = ''
  try { [sessions.value, conversations.value] = await Promise.all([api('/sessions'), api('/conversations')]) }
  catch (e) { apiError.value = e.message }
  finally { historyLoading.value = false }
}

async function navigate(destination) {
  if (exerciseOpen.value) {
    const ok = await finish('stop', 'user')
    if (!ok) return
  }
  page.value = destination
  if (destination === 'history') await loadHistory()
  if (destination === 'helper' && conversationId.value) await loadMessages()
  await focusTitle()
}

async function start() {
  if (initializing.value || busy.value || pendingEvent.value) return
  busy.value = true
  saveError.value = ''
  notice.value = ''
  outcome.value = null
  setupSeconds.value = null
  startRequestId ||= crypto.randomUUID()
  const body = pendingStart.value || { request_id: startRequestId, cue_mode: cue.value }
  pendingStart.value = body
  try {
    const result = await api('/sessions', { method: 'POST', body })
    current.value = result
    pendingStart.value = null
    startRequestId = null
    seconds.value = 0
    paused.value = false
    page.value = 'practice'
    // If a timed-out start already reached SQLite, do not count an unseen interval as practice.
    if (Date.now() - Date.parse(result.started_at) > 5000) {
      pacer.start()
      notice.value = 'The start confirmation was delayed. This session is stopped; start again when ready.'
      await finish('stop', 'timing_interruption')
    } else {
      beginTicks()
      await focusTitle()
    }
  } catch (e) { saveError.value = e.message }
  finally { busy.value = false }
}

async function sendEvent() {
  const saved = pendingEvent.value
  if (!saved) return false
  saveError.value = ''
  try {
    const result = await api(`/sessions/${saved.id}/events`, { method: 'POST', body: saved.body })
    current.value = result
    pendingEvent.value = null
    if (['completed', 'stopped'].includes(result.status)) {
      outcome.value = result
      current.value = null
      paused.value = false
      ending.value = false
      await focusTitle()
    }
    return true
  } catch (e) {
    saveError.value = e.message
    return false
  }
}

async function finish(action, reason = 'user') {
  if (!current.value) return true
  if (pendingEvent.value) return false
  ending.value = true
  stopTicks()
  seconds.value = pacer.pause()
  paused.value = true
  pendingEvent.value = {
    id: current.value.id,
    body: { request_id: crypto.randomUUID(), action, expected_version: current.value.version,
      reason, observed_seconds: reason === 'refresh' ? null : seconds.value },
  }
  return sendEvent()
}

async function pause(reason = 'user') {
  if (!current.value || paused.value || pendingEvent.value) return
  stopTicks()
  seconds.value = pacer.pause()
  paused.value = true
  pendingEvent.value = { id: current.value.id, body: { request_id: crypto.randomUUID(), action: 'pause', expected_version: current.value.version, reason } }
  await sendEvent()
}

async function resume() {
  if (!current.value || pendingEvent.value || busy.value) return
  busy.value = true
  pendingEvent.value = { id: current.value.id, body: { request_id: crypto.randomUUID(), action: 'resume', expected_version: current.value.version, reason: 'user' } }
  const ok = await sendEvent()
  if (ok) { paused.value = false; beginTicks(true) }
  busy.value = false
}

async function retryEvent() {
  if (busy.value) return
  const action = pendingEvent.value?.body.action
  busy.value = true
  const ok = await sendEvent()
  if (ok && action === 'resume') { paused.value = false; beginTicks(true) }
  busy.value = false
}

function openSupport() {
  supportDialog.value.showModal()
  if (exerciseOpen.value && !paused.value) pause('support')
}

async function savePreference() {
  preferenceBusy.value = true
  preferenceStatus.value = ''
  try {
    await api('/preferences', { method: 'PUT', body: { cue_mode: cue.value, remember: remember.value } })
    preferenceStatus.value = remember.value ? 'Cue choice saved for this fictional demo user. You can change it here.' : 'Saved cue choice forgotten. Your current choice still works for this visit.'
  } catch (e) { preferenceStatus.value = `Not saved: ${e.message}` }
  finally { preferenceBusy.value = false }
}

async function loadMessages() {
  if (!conversationId.value) return
  try { messages.value = await api(`/conversations/${conversationId.value}/messages`) }
  catch (e) { askError.value = e.message }
}

async function ensureConversation() {
  if (!conversationId.value) {
    const result = await api('/conversations', { method: 'POST', body: { request_id: newConversationRequest.value } })
    conversationId.value = result.id
    localStorage.setItem('breathing-conversation', result.id)
  }
}

function acceptAnswer(result) {
  retrieval.value = result
  askError.value = result.error || ''
  requestRecoverable.value = false
}

async function submitQuestion(retry = false) {
  if (askBusy.value || (!retry && !question.value.trim())) return
  askBusy.value = true
  askError.value = ''
  if (!retry) lastRequest.value = { request_id: crypto.randomUUID(), content: question.value.trim(), simulate_failure: isMock.value && simulateFailure.value }
  try {
    await ensureConversation()
    const result = await api(`/conversations/${conversationId.value}/messages`, { method: 'POST', body: lastRequest.value, timeout: 50000 })
    acceptAnswer(result)
    if (result.status === 'pending') {
      askError.value = 'The saved request is still pending. Check its status; do not submit it again with a new ID.'
      requestRecoverable.value = true
    }
    question.value = ''
    await loadMessages()
    health.value = await api('/health')
  } catch (e) { askError.value = e.message; requestRecoverable.value = true; await loadMessages() }
  finally { askBusy.value = false }
}

async function checkRequest() {
  if (!lastRequest.value || !conversationId.value || askBusy.value) return
  askBusy.value = true
  try {
    const result = await api(`/conversations/${conversationId.value}/requests/${lastRequest.value.request_id}`)
    acceptAnswer(result)
    if (result.status === 'pending') { askError.value = 'Still pending. You can check again.'; requestRecoverable.value = true }
    await loadMessages()
  } catch (e) { askError.value = e.message; requestRecoverable.value = true }
  finally { askBusy.value = false }
}

async function selectConversation(id) {
  if (askBusy.value) return
  conversationId.value = id
  localStorage.setItem('breathing-conversation', id)
  retrieval.value = null
  askError.value = ''
  lastRequest.value = null
  page.value = 'helper'
  await loadMessages()
  await focusTitle()
}

function newConversation() {
  if (askBusy.value) return
  conversationId.value = ''
  messages.value = []
  retrieval.value = null
  lastRequest.value = null
  askError.value = ''
  requestRecoverable.value = false
  newConversationRequest.value = crypto.randomUUID()
  localStorage.removeItem('breathing-conversation')
}

function visibilityChanged() {
  if (document.hidden && exerciseOpen.value && !paused.value && !ending.value) {
    notice.value = 'Exercise paused because the page was hidden. Resume when you are ready.'
    pause('hidden')
  }
}
function beforeUnload(event) {
  if (exerciseOpen.value || pendingEvent.value || pendingStart.value) { event.preventDefault(); event.returnValue = '' }
}
function mediaChanged(e) { reducedMotion.value = e.matches }

onMounted(async () => {
  media = window.matchMedia('(prefers-reduced-motion: reduce)')
  reducedMotion.value = media.matches
  media.addEventListener('change', mediaChanged)
  document.addEventListener('visibilitychange', visibilityChanged)
  window.addEventListener('beforeunload', beforeUnload)
  try {
    health.value = await api('/health')
    const preference = await api('/preferences')
    cue.value = preference.cue_mode
    remember.value = preference.remember
    await loadHistory()
    // An interrupted/closed tab must not appear as a completed exercise.
    const interrupted = sessions.value.filter(s => ['active', 'paused'].includes(s.status))
    for (const session of interrupted) {
      current.value = session
      pacer.start(session.active_seconds)
      pacer.pause()
      const ok = await finish('stop', 'refresh')
      if (!ok) break
    }
    if (interrupted.length) notice.value = 'An earlier interrupted session was marked stopped. No completion was assumed.'
  } catch (e) { apiError.value = e.message }
  finally { initializing.value = false }
})
onBeforeUnmount(() => {
  stopTicks()
  media?.removeEventListener('change', mediaChanged)
  document.removeEventListener('visibilitychange', visibilityChanged)
  window.removeEventListener('beforeunload', beforeUnload)
})
</script>

<template>
  <a class="skip" href="#main">Skip to content</a>
  <div class="shell">
    <header class="topbar">
      <button class="brand" @click="navigate('practice')" aria-label="Breathing Break home"><span class="brand-mark" aria-hidden="true"></span>Breathing Break</button>
      <button class="support-button" @click="openSupport">Crisis support information <span aria-hidden="true">↗</span></button>
    </header>
    <nav class="navigation" aria-label="Main">
      <button :aria-current="page === 'practice' ? 'page' : undefined" @click="navigate('practice')">Practice</button>
      <button :aria-current="page === 'history' ? 'page' : undefined" @click="navigate('history')">Saved history</button>
      <button :aria-current="page === 'helper' ? 'page' : undefined" @click="navigate('helper')">Exercise helper</button>
    </nav>
    <div class="prototype-note"><span class="dot" aria-hidden="true"></span>Coursework prototype · Fictional scenarios only · Not therapy or a monitored service</div>
    <p v-if="apiError" class="error" role="alert">{{ apiError }} <button class="text-button" @click="loadHistory">Retry connection</button></p>
    <p v-if="notice" class="notice" role="status">{{ notice }}</p>

    <main id="main">
      <section v-if="page === 'practice'" class="practice-layout" :class="{ 'in-session': exerciseOpen }">
        <div class="intro">
          <p class="eyebrow">A MOMENT BEFORE WHAT’S NEXT</p>
          <h1 v-if="!exerciseOpen && !outcome" ref="title" tabindex="-1">A short<br>breathing break.</h1>
          <h1 v-else-if="exerciseOpen" ref="title" tabindex="-1">{{ paused ? 'Take your time.' : 'One breath\nat a time.' }}</h1>
          <h1 v-else ref="title" tabindex="-1">{{ outcome.status === 'completed' ? 'You can finish here.' : 'You can leave it here.' }}</h1>
          <p class="lead">A simple 4–6 breathing exercise. Nothing to explain, and no need to finish.</p>
          <div class="scenario"><span class="eyebrow">FICTIONAL SCENARIO</span><p>A student takes a short break before a presentation.</p></div>
          <details class="about"><summary>About this exercise</summary><p>Breathe in for four one-second counts, then out for six. Repeat six times. No breath holds. The exercise sequence takes about one minute; setup and voluntary pauses are separate.</p><p>The sequence is fixed by the application. The helper cannot change it.</p></details>
        </div>

        <section class="practice-card" aria-label="Breathing exercise">
          <template v-if="exerciseOpen">
            <div class="card-top"><span class="pill">{{ ending ? 'Saving outcome' : paused ? 'Paused' : `Cycle ${view.cycle} of 6` }}</span><span class="elapsed" data-testid="elapsed">{{ Math.min(seconds, 999).toFixed(1) }} s active</span></div>
            <h2 class="phase" aria-live="polite">{{ ending ? 'Exercise ended' : paused ? 'Exercise paused' : view.phase }}</h2>
            <div v-if="cueVisible" class="orb-stage" aria-hidden="true"><div class="orb-outline"></div><div class="orb" :style="{ transform: `scale(${view.scale})` }"></div></div>
            <div v-else class="text-cue" aria-hidden="true">{{ view.count }}<span>/ {{ view.total }}</span></div>
            <p class="count" aria-hidden="true">{{ ending || paused ? 'Continue only when you choose.' : `${view.count} of ${view.total} counts` }}</p>
            <div class="exercise-actions"><button class="primary" :disabled="!!pendingEvent || busy || ending" @click="paused ? resume() : pause()">{{ paused ? 'Resume exercise' : 'Pause' }}</button><button class="secondary" :disabled="!!pendingEvent || ending" @click="finish('stop')">Stop exercise</button></div>
            <button class="text-button cue-switch" @click="cue = cue === 'circle' ? 'text' : 'circle'">{{ cueVisible ? 'Use text-only cues' : 'Use circle cue' }}</button>
            <p v-if="reducedMotion" class="small">Your device’s reduced-motion preference keeps the circle hidden.</p>
          </template>

          <template v-else-if="outcome">
            <div class="card-top"><span class="pill">{{ outcome.status === 'completed' ? 'Completed' : 'Stopped' }}</span><span>Saved in SQLite</span></div>
            <h2>{{ outcome.status === 'completed' ? 'Session complete.' : 'Session stopped.' }}</h2>
            <p class="outcome-number">{{ duration(outcome.active_seconds) }}</p>
            <p>Recorded active duration · {{ outcome.cycles_completed }} full cycles</p>
            <p v-if="outcome.observed_seconds !== null" class="small">Browser-measured guided time: {{ duration(outcome.observed_seconds) }}. Paused time: {{ duration(outcome.paused_seconds) }}.</p>
            <p v-if="setupSeconds !== null" class="small" data-testid="setup-time">This visit’s entry/setup before the first cue: {{ duration(setupSeconds) }}. This is separate from guided time.</p>
            <p v-else class="small">An interrupted page cannot establish guided duration. The recorded server interval may include time after the page closed.</p>
            <div class="stack"><button class="primary" @click="start" :disabled="busy">{{ busy ? 'Starting…' : 'Start another session' }}</button><button class="secondary" @click="outcome = null">Finish</button><button class="text-button" @click="navigate('history')">View saved session</button></div>
            <details class="record-id"><summary>Session record ID</summary><code>{{ outcome.id }}</code></details>
          </template>

          <template v-else>
            <div class="card-top"><span class="pill">4 in · 6 out</span><span>About 1 minute</span></div>
            <div class="orb-stage still" aria-hidden="true"><div class="orb-outline"></div><div class="orb"></div><span class="orb-label">a little space<br>to pause</span></div>
            <h2>Follow a steady pace.</h2>
            <p>Breathe in for 4 counts.<br>Breathe out for 6 counts.</p>
            <button class="primary full" @click="start" :disabled="busy || initializing">{{ initializing ? 'Connecting to local storage…' : busy ? 'Preparing your session…' : pendingStart ? 'Retry starting safely' : 'Start breathing' }} <span aria-hidden="true">→</span></button>
            <p class="permission">You can stop whenever you want.</p>
            <details class="preferences"><summary>Cue preference</summary><fieldset><legend>How would you like to follow the pace?</legend><label><input type="radio" v-model="cue" value="circle"> Circle and counts</label><label><input type="radio" v-model="cue" value="text"> Text-only counts</label></fieldset><label class="check"><input type="checkbox" v-model="remember"> Remember this cue choice for the fictional demo user</label><button class="secondary" :disabled="preferenceBusy" @click="savePreference">{{ preferenceBusy ? 'Saving…' : remember ? 'Save preference' : 'Forget saved preference' }}</button><p class="small" role="status">{{ preferenceStatus }}</p><p v-if="reducedMotion" class="small">Reduced motion is enabled on your device; text-only cues will be used.</p></details>
          </template>
          <div v-if="saveError" class="error" role="alert"><p>{{ saveError }}</p><p>The pacing is stopped while saving is unconfirmed.</p><button v-if="pendingEvent" class="secondary" @click="retryEvent" :disabled="busy">Retry saving safely</button></div>
        </section>
      </section>

      <section v-else-if="page === 'history'" class="history-page">
        <div class="section-heading"><div><p class="eyebrow">YOUR FICTIONAL DEMO RECORDS</p><h1 ref="title" tabindex="-1">Saved history.</h1></div><button class="secondary" @click="loadHistory" :disabled="historyLoading">{{ historyLoading ? 'Loading…' : 'Refresh history' }}</button></div>
        <p>These records describe practice activity. They do not measure mental health or improvement. The latest 100 sessions and conversations are shown.</p>
        <p v-if="apiError" class="small">Previously loaded records may be out of date while the API is unavailable.</p>
        <h2>Breathing sessions</h2>
        <p v-if="!sessions.length && !historyLoading" class="empty">No sessions saved yet. Start a breathing exercise when you choose.</p>
        <div v-else class="table-wrap"><table><caption class="sr-only">Session records from SQLite</caption><thead><tr><th scope="col">Started</th><th scope="col">Status</th><th scope="col">Active time</th><th scope="col">Paused time</th><th scope="col">Details</th></tr></thead><tbody><tr v-for="s in sessions" :key="s.id"><td>{{ timestamp(s.started_at) }}</td><td><span class="pill">{{ s.status }}</span></td><td>{{ duration(s.active_seconds) }}</td><td>{{ duration(s.paused_seconds) }}</td><td><details><summary>Record</summary><code>{{ s.id }}</code><p>{{ s.cue_mode }} cue · {{ s.cycles_completed }} cycles</p><p v-if="s.observed_seconds !== null">Browser: {{ duration(s.observed_seconds) }}</p><p v-if="s.stop_reason">Reason: {{ s.stop_reason }}</p></details></td></tr></tbody></table></div>
        <h2>Conversations</h2><p v-if="!conversations.length" class="empty">No conversations saved yet. The exercise works without chatting.</p><ul class="conversation-list"><li v-for="c in conversations" :key="c.id"><button class="secondary" @click="selectConversation(c.id)">Open conversation · {{ timestamp(c.created_at) }}</button><code>{{ c.id }}</code></li></ul>
      </section>

      <section v-else class="helper-page">
        <p class="eyebrow">OPTIONAL · OUTSIDE THE TIMED EXERCISE</p><h1 ref="title" tabindex="-1">Exercise helper.</h1>
        <div class="helper-status"><span class="pill">{{ health ? isMock ? 'Mock assistant' : 'Live API mode' : 'API connection unavailable' }}</span><p v-if="isMock">Scripted demonstration, not a live model. No paid calls are made.</p><p v-else-if="health?.live_verified">A live model reply was saved successfully during this server run.</p><p v-else>Live API configuration is separate from proof of a successful live call.</p></div>
        <p>Ask about the reviewed breathing exercise or this fictional demo user’s saved sessions. This helper does not provide therapy or monitor anyone.</p>
        <details class="about"><summary>Read the exercise without the helper</summary><p>Inhale for four counts and exhale for six, repeating six times. You can stop at any time. Use text-only cues if you prefer. No chat is required to start.</p></details>
        <div class="chat-toolbar"><button class="secondary" @click="newConversation" :disabled="askBusy">New conversation</button><button class="text-button" @click="loadMessages" :disabled="!conversationId || askBusy">Refresh messages</button><span v-if="conversationId" class="small">Conversation <code>{{ conversationId }}</code></span></div>
        <ol class="messages" aria-label="Conversation messages"><li v-for="m in messages" :key="m.id" :class="m.role"><div class="message-meta"><strong>{{ m.role === 'user' ? 'Fictional student' : m.provider_mode === 'mock' ? 'Mock helper' : m.provider_mode === 'static-boundary' ? 'Static boundary response' : 'Model helper' }}</strong><time :datetime="m.created_at">{{ timestamp(m.created_at) }}</time><span>{{ m.status }}</span></div><p>{{ m.content }}</p><details><summary>Message record</summary><code>{{ m.id }}</code><p v-if="m.record_ids.length">Supporting records: {{ m.record_ids.join(', ') }}</p></details></li></ol>
        <form @submit.prevent="submitQuestion()"><label for="question">Your fictional question</label><textarea id="question" v-model="question" maxlength="1000" rows="3" placeholder="For example: What did I do in my last session?" :disabled="askBusy"></textarea><div class="form-actions"><button class="primary" :disabled="askBusy || !question.trim()">{{ askBusy ? 'Waiting for the helper…' : 'Send question' }}</button><span class="small">{{ question.length }}/1000 characters</span></div><label v-if="isMock" class="check failure-switch"><input type="checkbox" v-model="simulateFailure" :disabled="askBusy"> Simulate a failed model request (coursework check)</label></form>
        <div v-if="askError" class="error" role="alert"><p>{{ askError }}</p><p v-if="retrieval?.status === 'failed'">Your submitted question is saved as failed. No assistant reply was fabricated.</p><div v-if="requestRecoverable" class="form-actions"><button class="secondary" @click="checkRequest" :disabled="askBusy">Check saved request</button><button class="secondary" @click="submitQuestion(true)" :disabled="askBusy">Retry same request ID</button></div></div>
        <details v-if="retrieval" class="retrieval"><summary>How this answer used stored context</summary><p>Request status: {{ retrieval.status }}. {{ retrieval.retrieval.length }} retrieved records. {{ isMock ? 'Mock planning and answer generation.' : 'At most two provider calls.' }}</p><p v-if="retrieval.query">Validated read-only query:</p><pre v-if="retrieval.query">{{ retrieval.query }}</pre><pre>{{ JSON.stringify(retrieval.retrieval, null, 2) }}</pre></details>
      </section>
    </main>
    <footer class="footer"><span>Designed for a fictional classroom scenario.<br>No one is monitoring this prototype.</span><span>{{ health && !apiError ? `Local API connected · ${health.model_mode} mode` : 'Local API connection unconfirmed' }}</span></footer>
  </div>

  <dialog ref="supportDialog" class="support-dialog" aria-labelledby="support-title" @close="focusTitle">
    <p class="eyebrow">INDEPENDENT SUPPORT ROUTE</p><h2 id="support-title">Crisis support information</h2><p>This information is separate from the coursework helper and works without a model response.</p><h3>{{ support.name }}</h3><p>{{ support.description }}</p><p><strong>Region:</strong> {{ support.region }}. Other regions may have different services.</p><div class="support-links"><a v-for="link in support.links" :key="link.href" :href="link.href" :target="link.href.startsWith('https') ? '_blank' : undefined" rel="noopener noreferrer">{{ link.text }} <span aria-hidden="true">↗</span></a></div><p class="small">Resource details verified October 22, 2026. This coursework app is not an emergency or crisis service and is not monitored.</p><p v-if="exerciseOpen">Your breathing exercise is paused. Returning will not resume it automatically.</p><div v-if="saveError" class="error" role="alert">{{ saveError }} Pause/stop saving is unconfirmed; the local pacing is stopped.</div><button class="primary full" @click="supportDialog.close()">{{ exerciseOpen ? 'Return to paused exercise' : 'Return to prototype' }}</button>
  </dialog>
</template>
