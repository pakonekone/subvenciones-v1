// API configuration
// In production (Vercel), use VITE_API_URL env var
// In development, use relative URLs (proxied by Vite)
export const API_BASE_URL = import.meta.env.VITE_API_URL || '';

export const getApiUrl = (path: string) => {
  // Remove leading slash if present to avoid double slashes
  const cleanPath = path.startsWith('/') ? path : `/${path}`;
  return `${API_BASE_URL}${cleanPath}`;
};
