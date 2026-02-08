const API_BASE = (process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000').replace(/\/$/, '');
const API_PREFIX = `${API_BASE}/api/v1`;

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_PREFIX}${path}`, {
    cache: 'no-store',
    headers: {
      'Content-Type': 'application/json',
      ...(init?.headers || {}),
    },
    ...init,
  });

  if (!response.ok) {
    throw new Error(`API request failed: ${response.status}`);
  }

  if (response.status === 204) {
    return {} as T;
  }
  return (await response.json()) as T;
}

export function apiGet<T>(path: string, init?: RequestInit): Promise<T> {
  return request<T>(path, { method: 'GET', ...init });
}

export function apiPost<T>(path: string, body?: unknown, init?: RequestInit): Promise<T> {
  return request<T>(path, {
    method: 'POST',
    body: body ? JSON.stringify(body) : undefined,
    ...init,
  });
}
