import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

const api = axios.create({
  baseURL: API_URL,
  headers: { 'Content-Type': 'application/json' },
  withCredentials: true,  // Important: send cookies with every request
});

// Request caching for GET requests to eliminate duplicate calls
const requestCache = new Map();
const CACHE_DURATION = 30000; // 30 seconds

// Cache CSRF token in memory (received from login response)
let cachedCSRFToken = null;

// Attach CSRF token and cache GET requests
api.interceptors.request.use((config) => {
  // Attach CSRF token for state-changing requests (POST, PUT, DELETE, PATCH)
  if (cachedCSRFToken && ['post', 'put', 'delete', 'patch'].includes(config.method)) {
    config.headers['X-CSRF-Token'] = cachedCSRFToken;
  }
  
  // Handle GET request caching for deduplication
  if (config.method === 'get') {
    const cacheKey = `${config.method}:${config.url}`;
    
    if (requestCache.has(cacheKey)) {
      const { timestamp, promise } = requestCache.get(cacheKey);
      // Return cached response if still fresh
      if (Date.now() - timestamp < CACHE_DURATION) {
        return Promise.reject({ __cachedResponse: promise });
      }
    }
    
    // Store the pending request promise for deduplication
    config._cacheKey = cacheKey;
  }
  
  return config;
});

// Auto-refresh on 401 + cache successful responses
api.interceptors.response.use(
  (res) => {
    // Cache successful GET responses
    if (res.config._cacheKey) {
      requestCache.set(res.config._cacheKey, {
        timestamp: Date.now(),
        promise: Promise.resolve(res),
      });
    }
    
    // Store CSRF token from login response
    if (res.data?.csrf_token) {
      cachedCSRFToken = res.data.csrf_token;
    }
    
    return res;
  },
  async (error) => {
    // Handle cached response rejection
    if (error.__cachedResponse) {
      return error.__cachedResponse;
    }
    
    const original = error.config;
    if (error.response?.status === 401 && !original._retry) {
      original._retry = true;
      try {
        // Refresh endpoint will use httpOnly cookies automatically
        const { data } = await axios.post(`${API_URL}/auth/refresh`, {}, {
          withCredentials: true,
        });
        
        // Update CSRF token from refresh response if provided
        if (data?.csrf_token) {
          cachedCSRFToken = data.csrf_token;
        }
        
        // Retry original request with new CSRF token if available
        if (cachedCSRFToken) {
          original.headers['X-CSRF-Token'] = cachedCSRFToken;
        }
        return api(original);
      } catch {
        // Clear CSRF token and redirect to login
        cachedCSRFToken = null;
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export default api;

