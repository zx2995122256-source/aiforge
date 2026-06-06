const BASE = '/api'

function getToken(): string | null {
  return localStorage.getItem('aiforge_token')
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken()
  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string> || {}),
  }

  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  if (!(options.body instanceof FormData)) {
    headers['Content-Type'] = 'application/json'
  }

  const controller = new AbortController()
  const timeout = setTimeout(() => controller.abort(), 600000)
  const isUpload = options.body instanceof FormData

  try {
    const res = await fetch(`${BASE}${path}`, {
      ...options,
      headers,
      signal: controller.signal,
    })

    if (!res.ok) {
      let message = `请求失败: ${res.status}`
      try {
        const data = await res.json()
        message = data.detail || data.message || message
      } catch {}
      const err = new Error(message) as Error & { status?: number }
      err.status = res.status
      throw err
    }

    if (res.status === 204) return undefined as T
    return res.json()
  } finally {
    clearTimeout(timeout)
  }
}

export function get<T>(path: string): Promise<T> {
  return request<T>(path, { method: 'GET' })
}

export function post<T>(path: string, body?: unknown): Promise<T> {
  return request<T>(path, {
    method: 'POST',
    body: body instanceof FormData ? body : JSON.stringify(body),
  })
}

export function upload<T>(path: string, formData: FormData): Promise<T> {
  return request<T>(path, {
    method: 'POST',
    body: formData,
  })
}

export function del<T>(path: string): Promise<T> {
  return request<T>(path, { method: 'DELETE' })
}

export function put<T>(path: string, body?: unknown): Promise<T> {
  return request<T>(path, {
    method: 'PUT',
    body: body instanceof FormData ? body : JSON.stringify(body),
  })
}
