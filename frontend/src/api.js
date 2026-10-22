export async function api(path, { method = 'GET', body, timeout = 12000 } = {}) {
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), timeout)
  try {
    const response = await fetch(`/api${path}`, {
      method,
      headers: body === undefined ? {} : { 'Content-Type': 'application/json' },
      body: body === undefined ? undefined : JSON.stringify(body),
      signal: controller.signal,
    })
    let data
    try { data = await response.json() }
    catch { throw new Error('The local API did not return a usable response. Saving is unconfirmed. Check that FastAPI is running, then retry safely.') }
    if (!response.ok) {
      throw new Error(typeof data.detail === 'string' ? data.detail : 'The request was not accepted. Check the input and retry.')
    }
    return data
  } catch (error) {
    if (error.name === 'AbortError') throw new Error('The request timed out. Saving is unconfirmed. Retry the same request to check it safely.')
    if (error instanceof TypeError) throw new Error('The local API is unavailable. Saving is unconfirmed. Support information is still available.')
    throw error
  } finally { clearTimeout(timer) }
}
