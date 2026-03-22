/**
 * API configuration
 */
export const API_CONFIG = {
  baseURL: import.meta.env.VITE_API_URL || '/api',
  timeout: 30000,
  uploadTimeout: 120000,
  queryTimeout: 60000,
};
