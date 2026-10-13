/**
 * Blog API Client
 * Configured using modern `fetch` with JWT token management and automatic refresh
 */

class ApiClient {
  constructor() {
    this.baseUrl = window.API_BASE_URL || (
      window.location.origin.includes(':8000')
        ? '/api/v1'
        : 'http://localhost:8000/api/v1'
    );
    this.accessTokenKey = 'blog_access_token';
    this.refreshTokenKey = 'blog_refresh_token';
    this.userKey = 'blog_user';
    this.isRefreshing = false;
    this.refreshSubscribers = [];
  }

  // --- Token Management ---

  getAccessToken() {
    return localStorage.getItem(this.accessTokenKey);
  }

  getRefreshToken() {
    return localStorage.getItem(this.refreshTokenKey);
  }

  setTokens(accessToken, refreshToken) {
    if (accessToken) localStorage.setItem(this.accessTokenKey, accessToken);
    if (refreshToken) localStorage.setItem(this.refreshTokenKey, refreshToken);
  }

  getUser() {
    const raw = localStorage.getItem(this.userKey);
    try {
      return raw ? JSON.parse(raw) : null;
    } catch {
      return null;
    }
  }

  setUser(user) {
    if (user) {
      localStorage.setItem(this.userKey, JSON.stringify(user));
    } else {
      localStorage.removeItem(this.userKey);
    }
  }

  clearAuth() {
    localStorage.removeItem(this.accessTokenKey);
    localStorage.removeItem(this.refreshTokenKey);
    localStorage.removeItem(this.userKey);
    window.dispatchEvent(new CustomEvent('auth:change', { detail: { user: null } }));
  }

  isAuthenticated() {
    return Boolean(this.getAccessToken());
  }

  // --- Core Fetch Wrapper ---

  async request(endpoint, options = {}) {
    const url = `${this.baseUrl}${endpoint}`;
    const headers = { ...options.headers };

    // Attach Bearer Token if available
    const token = this.getAccessToken();
    if (token && !headers['Authorization']) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    // Default to JSON body if not form-encoded or FormData
    if (
      options.body &&
      typeof options.body === 'object' &&
      !(options.body instanceof FormData) &&
      !(options.body instanceof URLSearchParams)
    ) {
      headers['Content-Type'] = 'application/json';
      options.body = JSON.stringify(options.body);
    }

    try {
      let response = await fetch(url, { ...options, headers });

      // Handle 401 Unauthorized -> Attempt token refresh
      if (response.status === 401 && this.getRefreshToken() && !endpoint.includes('/auth/refresh') && !endpoint.includes('/auth/login')) {
        const refreshed = await this.refreshToken();
        if (refreshed) {
          headers['Authorization'] = `Bearer ${this.getAccessToken()}`;
          response = await fetch(url, { ...options, headers });
        } else {
          this.clearAuth();
          throw new Error('Session expired. Please log in again.');
        }
      }

      // Handle 204 No Content
      if (response.status === 204) {
        return null;
      }

      const data = await response.json().catch(() => null);

      if (!response.ok) {
        const errorMessage = (data && (data.detail || data.message))
          ? (typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail))
          : `Request failed with status ${response.status}`;
        const error = new Error(errorMessage);
        error.status = response.status;
        error.data = data;
        throw error;
      }

      return data;
    } catch (err) {
      throw err;
    }
  }

  async refreshToken() {
    const refreshToken = this.getRefreshToken();
    if (!refreshToken) return false;

    try {
      const response = await fetch(`${this.baseUrl}/auth/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: refreshToken })
      });

      if (!response.ok) {
        return false;
      }

      const data = await response.json();
      if (data.access_token) {
        this.setTokens(data.access_token, data.refresh_token || refreshToken);
        return true;
      }
      return false;
    } catch {
      return false;
    }
  }

  // --- Auth Endpoints ---

  auth = {
    register: async ({ username, email, password }) => {
      const user = await this.request('/auth/register', {
        method: 'POST',
        body: { username, email, password }
      });
      return user;
    },

    login: async ({ username, password }) => {
      const body = new URLSearchParams();
      body.append('username', username);
      body.append('password', password);

      const tokens = await this.request('/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body
      });

      this.setTokens(tokens.access_token, tokens.refresh_token);

      // Fetch user profile immediately
      const user = await this.users.getMe();
      this.setUser(user);
      window.dispatchEvent(new CustomEvent('auth:change', { detail: { user } }));
      return { tokens, user };
    },

    logout: () => {
      this.clearAuth();
    }
  };

  // --- Users Endpoints ---

  users = {
    getMe: async () => {
      return await this.request('/users/me', { method: 'GET' });
    }
  };

  // --- Posts Endpoints ---

  posts = {
    list: async ({ page = 1, perPage = 9, tagSlug = '', search = '', authorId = null } = {}) => {
      const params = new URLSearchParams();
      params.append('page', page);
      params.append('per_page', perPage);
      if (tagSlug) params.append('tag_slug', tagSlug);
      if (search) params.append('search', search);
      if (authorId) params.append('author_id', authorId);

      return await this.request(`/posts/?${params.toString()}`, { method: 'GET' });
    },

    getBySlug: async (slug) => {
      return await this.request(`/posts/${encodeURIComponent(slug)}`, { method: 'GET' });
    },

    create: async ({ title, content, excerpt = '', is_published = true, tags = [] }) => {
      return await this.request('/posts/', {
        method: 'POST',
        body: { title, content, excerpt, is_published, tags }
      });
    },

    update: async (slug, data) => {
      return await this.request(`/posts/${encodeURIComponent(slug)}`, {
        method: 'PATCH',
        body: data
      });
    },

    delete: async (slug) => {
      return await this.request(`/posts/${encodeURIComponent(slug)}`, {
        method: 'DELETE'
      });
    },

    toggleLike: async (postId) => {
      return await this.request(`/posts/${postId}/like`, {
        method: 'POST'
      });
    }
  };

  // --- Comments Endpoints ---

  comments = {
    list: async (postId) => {
      return await this.request(`/posts/${postId}/comments`, { method: 'GET' });
    },

    create: async (postId, { text, parent_id = null }) => {
      return await this.request(`/posts/${postId}/comments`, {
        method: 'POST',
        body: { text, parent_id }
      });
    },

    update: async (commentId, text) => {
      return await this.request(`/comments/${commentId}`, {
        method: 'PATCH',
        body: { text }
      });
    },

    delete: async (commentId) => {
      return await this.request(`/comments/${commentId}`, {
        method: 'DELETE'
      });
    }
  };

  // --- Tags Endpoints ---

  tags = {
    list: async () => {
      return await this.request('/tags/', { method: 'GET' });
    },

    create: async (name) => {
      return await this.request('/tags/', {
        method: 'POST',
        body: { name }
      });
    }
  };
}

// Global instance for browser script execution
window.api = new ApiClient();
