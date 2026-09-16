// API utility functions (placeholder - to be implemented when backend APIs are available)
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1';

export async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  
  const config: RequestInit = {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    credentials: 'include', // For session-based auth with cookies
  };

  const response = await fetch(url, config);

  if (!response.ok) {
    const error = await response.json().catch(() => ({
      message: 'An error occurred',
    }));
    throw new Error(error.message || 'Request failed');
  }

  return response.json();
}

// TODO: Implement specific API functions when backend endpoints are available
// export const authAPI = { ... }
// export const propertiesAPI = { ... }
// export const bookingsAPI = { ... }
