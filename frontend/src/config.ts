export const config = {
  apiBaseURL: import.meta.env.VITE_API_BASE_URL ?? "/api",
  apiTimeout: Number(import.meta.env.VITE_API_TIMEOUT ?? 30000),
  pollInterval: Number(import.meta.env.VITE_POLL_INTERVAL ?? 1000),
} as const;
