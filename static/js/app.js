/**
 * Blog Platform - Main Application Controller
 */

// Application State
const state = {
  currentPage: 1,
  perPage: 9,
  currentTag: '',
  searchQuery: '',
  currentPostSlug: null,
  tags: [],
  user: null
};

// --- Toast System ---
function showToast(message, type = 'info') {
  const container = document.getElementById('toast-container');
  if (!container) return;

  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  const icon = type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle';
  toast.innerHTML = `<i class="fa-solid fa-${icon}"></i> <span>${escapeHtml(message)}</span>`;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(100%)';
    toast.style.transition = 'all 0.3s ease-out';
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

// Helper: Escape HTML
function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

// Helper: Format Date
function formatDate(isoStr) {
  if (!isoStr) return '';
  const date = new Date(isoStr);
  return date.toLocaleDateString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  });
}

// --- Auth UI Management ---
function updateAuthUI() {
  const navActions = document.getElementById('nav-actions');
  const user = window.api.getUser();
  state.user = user;

  const adminUrl = window.location.protocol === 'file:' ? 'http://localhost:8000/admin' : '/admin';

  if (user) {
    navActions.innerHTML = `
      <button class="btn btn-primary btn-sm" id="btn-new-post">
        <i class="fa-solid fa-pen-to-square"></i> New Post
      </button>
      <div class="user-badge">
        <div class="user-avatar">${user.username.charAt(0).toUpperCase()}</div>
        <span>${escapeHtml(user.username)}</span>
      </div>
      <a href="${adminUrl}" target="_blank" class="btn btn-outline btn-sm" title="Admin Panel">
        <i class="fa-solid fa-shield-halved"></i> Admin
      </a>
      <button class="btn btn-ghost btn-sm" id="btn-logout" title="Log Out">
        <i class="fa-solid fa-arrow-right-from-bracket"></i>
      </button>
    `;

    document.getElementById('btn-new-post')?.addEventListener('click', openNewPostModal);
    document.getElementById('btn-logout')?.addEventListener('click', () => {
      window.api.auth.logout();
      showToast('You have been logged out.', 'info');
      updateAuthUI();
      // If viewing detail of post you authored, re-render
      if (state.currentPostSlug) {
        loadPostDetail(state.currentPostSlug);
      }
    });
  } else {
    navActions.innerHTML = `
      <a href="${adminUrl}" target="_blank" class="btn btn-ghost btn-sm" title="Admin Panel">
        <i class="fa-solid fa-shield-halved"></i> Admin
      </a>
      <button class="btn btn-primary btn-sm" id="btn-open-auth">
        <i class="fa-solid fa-user"></i> Sign In
      </button>
    `;

    document.getElementById('btn-open-auth')?.addEventListener('click', () => openAuthModal('login'));
  }
}

// --- Tags Filter ---
async function loadTags() {
  try {
    const tags = await window.api.tags.list();
    state.tags = tags;
    const container = document.getElementById('tags-bar');
    if (!container) return;

    let html = `<button class="tag-pill ${!state.currentTag ? 'active' : ''}" data-tag="">All</button>`;
    tags.forEach(t => {
      const active = state.currentTag === t.slug ? 'active' : '';
      html += `<button class="tag-pill ${active}" data-tag="${escapeHtml(t.slug)}">#${escapeHtml(t.name)}</button>`;
    });
    container.innerHTML = html;

    container.querySelectorAll('.tag-pill').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const tag = e.currentTarget.getAttribute('data-tag');
        state.currentTag = tag;
        state.currentPage = 1;
        loadTags();
        loadPosts();
      });
    });
  } catch (err) {
    console.error('Failed to load tags:', err);
  }
}

// --- Posts Feed ---
async function loadPosts() {
  const container = document.getElementById('posts-container');
  const paginationContainer = document.getElementById('pagination');
  if (!container) return;

  container.innerHTML = `
    <div class="state-container">
      <div class="spinner"></div>
      <p>Loading posts...</p>
    </div>
  `;

  try {
    const res = await window.api.posts.list({
      page: state.currentPage,
      perPage: state.perPage,
      search: state.searchQuery,
      tagSlug: state.currentTag
    });

    const posts = res.items || [];
    const total = res.total || 0;

    if (posts.length === 0) {
      container.innerHTML = `
        <div class="state-container">
          <i class="fa-regular fa-folder-open" style="font-size: 2.5rem; margin-bottom: 0.75rem; color: var(--text-muted);"></i>
          <h3>No posts found</h3>
          <p>Try clearing your search or filters.</p>
        </div>
      `;
      if (paginationContainer) paginationContainer.innerHTML = '';
      return;
    }

    container.innerHTML = posts.map(post => `
      <article class="post-card" data-slug="${escapeHtml(post.slug)}">
        <div class="post-card-tags">
          ${(post.tags || []).map(t => `<span class="post-tag">#${escapeHtml(t.name)}</span>`).join('')}
        </div>
        <h3 class="post-card-title">${escapeHtml(post.title)}</h3>
        <p class="post-card-excerpt">${escapeHtml(post.excerpt || post.content || '')}</p>
        <div class="post-card-footer">
          <div class="post-meta-author">
            <i class="fa-regular fa-user"></i> ${escapeHtml(post.author?.username || 'Anonymous')}
          </div>
          <div class="post-meta-stats">
            <span class="stat-item" title="Views">
              <i class="fa-regular fa-eye"></i> ${post.views}
            </span>
            <button class="stat-item like-btn" data-id="${post.id}" title="Likes">
              <i class="fa-regular fa-heart"></i> ${post.like_count || 0}
            </button>
          </div>
        </div>
      </article>
    `).join('');

    // Attach card click handlers
    container.querySelectorAll('.post-card').forEach(card => {
      card.addEventListener('click', (e) => {
        // If clicking like button directly, do not open detail
        if (e.target.closest('.like-btn')) return;
        const slug = card.getAttribute('data-slug');
        showPostDetail(slug);
      });
    });

    // Attach card quick like handlers
    container.querySelectorAll('.like-btn').forEach(btn => {
      btn.addEventListener('click', async (e) => {
        e.stopPropagation();
        if (!window.api.isAuthenticated()) {
          openAuthModal('login');
          return;
        }
        const postId = btn.getAttribute('data-id');
        try {
          const result = await window.api.posts.toggleLike(postId);
          showToast(result.liked ? 'Liked post!' : 'Unliked post', 'info');
          loadPosts();
        } catch (err) {
          showToast(err.message, 'error');
        }
      });
    });

    // Render Pagination
    const totalPages = Math.ceil(total / state.perPage);
    if (totalPages > 1 && paginationContainer) {
      paginationContainer.innerHTML = `
        <button class="btn btn-outline btn-sm" id="prev-page" ${state.currentPage <= 1 ? 'disabled' : ''}>
          <i class="fa-solid fa-chevron-left"></i> Previous
        </button>
        <span style="font-size: 0.9rem; color: var(--text-secondary);">Page ${state.currentPage} of ${totalPages}</span>
        <button class="btn btn-outline btn-sm" id="next-page" ${state.currentPage >= totalPages ? 'disabled' : ''}>
          Next <i class="fa-solid fa-chevron-right"></i>
        </button>
      `;

      document.getElementById('prev-page')?.addEventListener('click', () => {
        if (state.currentPage > 1) {
          state.currentPage--;
          loadPosts();
          window.scrollTo({ top: 0, behavior: 'smooth' });
        }
      });

      document.getElementById('next-page')?.addEventListener('click', () => {
        if (state.currentPage < totalPages) {
          state.currentPage++;
          loadPosts();
          window.scrollTo({ top: 0, behavior: 'smooth' });
        }
      });
    } else if (paginationContainer) {
      paginationContainer.innerHTML = '';
    }

  } catch (err) {
    container.innerHTML = `
      <div class="state-container">
        <i class="fa-solid fa-triangle-exclamation" style="font-size: 2rem; color: var(--accent-danger); margin-bottom: 0.5rem;"></i>
        <p>Failed to load posts: ${escapeHtml(err.message)}</p>
      </div>
    `;
  }
}

// --- Post Detail & Comments View ---
async function showPostDetail(slug) {
  state.currentPostSlug = slug;
  document.getElementById('feed-view').style.display = 'none';
  const detailContainer = document.getElementById('detail-view');
  detailContainer.style.display = 'block';
  window.scrollTo({ top: 0, behavior: 'smooth' });

  detailContainer.innerHTML = `
    <div class="state-container">
      <div class="spinner"></div>
      <p>Loading post...</p>
    </div>
  `;

  try {
    const post = await window.api.posts.getBySlug(slug);
    renderPostDetail(post);
    loadComments(post.id);
  } catch (err) {
    detailContainer.innerHTML = `
      <div class="state-container">
        <p>Error loading post: ${escapeHtml(err.message)}</p>
        <button class="btn btn-outline btn-sm" id="btn-back-feed">Back to Feed</button>
      </div>
    `;
    document.getElementById('btn-back-feed')?.addEventListener('click', backToFeed);
  }
}

function renderPostDetail(post) {
  const container = document.getElementById('detail-view');
  const isAuthor = state.user && state.user.id === post.author?.id;

  container.innerHTML = `
    <button class="btn btn-outline btn-sm" id="btn-back-feed" style="margin-bottom: 1.5rem;">
      <i class="fa-solid fa-arrow-left"></i> Back to All Posts
    </button>

    <div class="detail-header">
      <div class="post-card-tags" style="margin-bottom: 1rem;">
        ${(post.tags || []).map(t => `<span class="post-tag">#${escapeHtml(t.name)}</span>`).join('')}
      </div>
      <h1 class="detail-title">${escapeHtml(post.title)}</h1>
      <div class="detail-meta">
        <span><i class="fa-regular fa-user"></i> ${escapeHtml(post.author?.username)}</span>
        <span><i class="fa-regular fa-calendar"></i> ${formatDate(post.created_at)}</span>
        <span><i class="fa-regular fa-eye"></i> ${post.views} views</span>
        <button class="btn btn-outline btn-sm" id="detail-like-btn">
          <i class="fa-regular fa-heart"></i> ${post.like_count || 0} Likes
        </button>
        ${isAuthor ? `
          <button class="btn btn-danger btn-sm" id="btn-delete-post">
            <i class="fa-solid fa-trash"></i> Delete Post
          </button>
        ` : ''}
      </div>
    </div>

    <div class="detail-content">${escapeHtml(post.content)}</div>

    <div class="comments-section">
      <h3 class="comments-title">
        <i class="fa-regular fa-comments"></i> Discussion
      </h3>

      <div class="comment-box">
        <textarea id="comment-input" class="form-textarea" style="min-height: 80px;" placeholder="${state.user ? 'Write a comment...' : 'Log in to join the discussion'}"></textarea>
        <div style="display: flex; justify-content: flex-end; margin-top: 0.75rem;">
          <button class="btn btn-primary btn-sm" id="btn-submit-comment" ${!state.user ? 'disabled' : ''}>
            Post Comment
          </button>
        </div>
      </div>

      <div id="comments-list">
        <div class="spinner"></div>
      </div>
    </div>
  `;

  document.getElementById('btn-back-feed')?.addEventListener('click', backToFeed);

  // Like button
  document.getElementById('detail-like-btn')?.addEventListener('click', async () => {
    if (!window.api.isAuthenticated()) {
      openAuthModal('login');
      return;
    }
    try {
      const res = await window.api.posts.toggleLike(post.id);
      showToast(res.liked ? 'Liked post!' : 'Unliked post', 'info');
      showPostDetail(post.slug);
    } catch (err) {
      showToast(err.message, 'error');
    }
  });

  // Delete post
  document.getElementById('btn-delete-post')?.addEventListener('click', async () => {
    if (!confirm('Are you sure you want to delete this post?')) return;
    try {
      await window.api.posts.delete(post.slug);
      showToast('Post deleted successfully.', 'success');
      backToFeed();
    } catch (err) {
      showToast(err.message, 'error');
    }
  });

  // Submit top-level comment
  document.getElementById('btn-submit-comment')?.addEventListener('click', async () => {
    const text = document.getElementById('comment-input').value.trim();
    if (!text) return;
    try {
      await window.api.comments.create(post.id, { text });
      document.getElementById('comment-input').value = '';
      showToast('Comment posted.', 'success');
      loadComments(post.id);
    } catch (err) {
      showToast(err.message, 'error');
    }
  });
}

function backToFeed() {
  state.currentPostSlug = null;
  document.getElementById('detail-view').style.display = 'none';
  document.getElementById('feed-view').style.display = 'block';
  loadPosts();
}

// --- Comments Tree ---
async function loadComments(postId) {
  const container = document.getElementById('comments-list');
  if (!container) return;

  try {
    const comments = await window.api.comments.list(postId);
    if (!comments || comments.length === 0) {
      container.innerHTML = `<p style="color: var(--text-muted); font-size: 0.9rem;">No comments yet. Be the first to start the discussion!</p>`;
      return;
    }

    container.innerHTML = comments.map(c => renderCommentNode(c, postId)).join('');

    // Attach reply button handlers
    container.querySelectorAll('.btn-reply-toggle').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const commentId = e.currentTarget.getAttribute('data-id');
        const replyBox = document.getElementById(`reply-box-${commentId}`);
        if (replyBox) {
          replyBox.style.display = replyBox.style.display === 'none' ? 'block' : 'none';
        }
      });
    });

    // Attach reply submit handlers
    container.querySelectorAll('.btn-submit-reply').forEach(btn => {
      btn.addEventListener('click', async (e) => {
        const commentId = e.currentTarget.getAttribute('data-id');
        const input = document.getElementById(`reply-input-${commentId}`);
        const text = input ? input.value.trim() : '';
        if (!text) return;
        try {
          await window.api.comments.create(postId, { text, parent_id: parseInt(commentId, 10) });
          showToast('Reply posted.', 'success');
          loadComments(postId);
        } catch (err) {
          showToast(err.message, 'error');
        }
      });
    });

    // Attach delete comment handlers
    container.querySelectorAll('.btn-delete-comment').forEach(btn => {
      btn.addEventListener('click', async (e) => {
        const commentId = e.currentTarget.getAttribute('data-id');
        if (!confirm('Delete this comment?')) return;
        try {
          await window.api.comments.delete(commentId);
          showToast('Comment deleted.', 'success');
          loadComments(postId);
        } catch (err) {
          showToast(err.message, 'error');
        }
      });
    });

  } catch (err) {
    container.innerHTML = `<p style="color: var(--accent-danger);">Failed to load comments: ${escapeHtml(err.message)}</p>`;
  }
}

function renderCommentNode(comment, postId) {
  const isAuthor = state.user && state.user.id === comment.author?.id;
  const hasReplies = comment.replies && comment.replies.length > 0;

  return `
    <div class="comment-item" id="comment-${comment.id}">
      <div class="comment-header">
        <span class="comment-author">
          <i class="fa-regular fa-user"></i> ${escapeHtml(comment.author?.username)}
        </span>
        <span class="comment-time">${formatDate(comment.created_at)}</span>
      </div>
      <div class="comment-body">${escapeHtml(comment.text)}</div>
      <div class="comment-actions">
        ${state.user ? `
          <button class="btn btn-ghost btn-sm btn-reply-toggle" data-id="${comment.id}">
            <i class="fa-solid fa-reply"></i> Reply
          </button>
        ` : ''}
        ${isAuthor ? `
          <button class="btn btn-ghost btn-sm btn-delete-comment" data-id="${comment.id}" style="color: var(--accent-danger);">
            <i class="fa-solid fa-trash"></i> Delete
          </button>
        ` : ''}
      </div>

      <div id="reply-box-${comment.id}" style="display: none; margin-top: 0.75rem;">
        <div style="display: flex; gap: 0.5rem;">
          <input type="text" id="reply-input-${comment.id}" class="form-input" placeholder="Write a reply..." />
          <button class="btn btn-primary btn-sm btn-submit-reply" data-id="${comment.id}">Send</button>
        </div>
      </div>

      ${hasReplies ? `
        <div class="replies-container">
          ${comment.replies.map(r => renderCommentNode(r, postId)).join('')}
        </div>
      ` : ''}
    </div>
  `;
}

// --- Modals: Auth & New Post ---

function openAuthModal(initialTab = 'login') {
  const modal = document.getElementById('auth-modal');
  if (!modal) return;
  modal.classList.add('active');
  switchAuthTab(initialTab);
}

function closeAuthModal() {
  document.getElementById('auth-modal')?.classList.remove('active');
}

function switchAuthTab(tab) {
  const loginForm = document.getElementById('form-login');
  const registerForm = document.getElementById('form-register');
  const tabLogin = document.getElementById('tab-login');
  const tabRegister = document.getElementById('tab-register');

  if (tab === 'login') {
    loginForm.style.display = 'block';
    registerForm.style.display = 'none';
    tabLogin.classList.add('active');
    tabRegister.classList.remove('active');
  } else {
    loginForm.style.display = 'none';
    registerForm.style.display = 'block';
    tabLogin.classList.remove('active');
    tabRegister.classList.add('active');
  }
}

function openNewPostModal() {
  if (!window.api.isAuthenticated()) {
    openAuthModal('login');
    return;
  }
  document.getElementById('new-post-modal')?.classList.add('active');
}

function closeNewPostModal() {
  document.getElementById('new-post-modal')?.classList.remove('active');
}

// --- Initialization ---
document.addEventListener('DOMContentLoaded', async () => {
  // 1. Initial Auth Check
  if (window.api.isAuthenticated() && !window.api.getUser()) {
    try {
      const user = await window.api.users.getMe();
      window.api.setUser(user);
    } catch {
      window.api.clearAuth();
    }
  }
  updateAuthUI();

  // 2. Load Feed & Tags
  loadTags();
  loadPosts();

  // 3. Search Bar Debounce
  const searchInput = document.getElementById('search-input');
  let debounceTimeout = null;
  searchInput?.addEventListener('input', (e) => {
    clearTimeout(debounceTimeout);
    debounceTimeout = setTimeout(() => {
      state.searchQuery = e.target.value.trim();
      state.currentPage = 1;
      loadPosts();
    }, 350);
  });

  // 4. Modal Close Events
  document.querySelectorAll('.modal-close').forEach(btn => {
    btn.addEventListener('click', () => {
      closeAuthModal();
      closeNewPostModal();
    });
  });

  document.querySelectorAll('.modal-overlay').forEach(overlay => {
    overlay.addEventListener('click', (e) => {
      if (e.target === overlay) {
        closeAuthModal();
        closeNewPostModal();
      }
    });
  });

  // Auth Tabs
  document.getElementById('tab-login')?.addEventListener('click', () => switchAuthTab('login'));
  document.getElementById('tab-register')?.addEventListener('click', () => switchAuthTab('register'));

  // Login Form Submission
  document.getElementById('form-login')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const username = document.getElementById('login-username').value.trim();
    const password = document.getElementById('login-password').value;
    const btn = e.target.querySelector('button[type="submit"]');
    btn.disabled = true;

    try {
      await window.api.auth.login({ username, password });
      showToast('Logged in successfully!', 'success');
      closeAuthModal();
      updateAuthUI();
      loadPosts();
    } catch (err) {
      showToast(err.message, 'error');
    } finally {
      btn.disabled = false;
    }
  });

  // Register Form Submission
  document.getElementById('form-register')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const username = document.getElementById('reg-username').value.trim();
    const email = document.getElementById('reg-email').value.trim();
    const password = document.getElementById('reg-password').value;
    const btn = e.target.querySelector('button[type="submit"]');
    btn.disabled = true;

    try {
      await window.api.auth.register({ username, email, password });
      showToast('Account created! Logging in...', 'success');
      // Auto login
      await window.api.auth.login({ username, password });
      closeAuthModal();
      updateAuthUI();
      loadPosts();
    } catch (err) {
      showToast(err.message, 'error');
    } finally {
      btn.disabled = false;
    }
  });

  // Create Post Form Submission
  document.getElementById('form-new-post')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const title = document.getElementById('post-title').value.trim();
    const excerpt = document.getElementById('post-excerpt').value.trim();
    const content = document.getElementById('post-content').value.trim();
    const tagsRaw = document.getElementById('post-tags').value.trim();
    const isPublished = document.getElementById('post-published').checked;
    const btn = e.target.querySelector('button[type="submit"]');
    btn.disabled = true;

    const tags = tagsRaw
      ? tagsRaw.split(',').map(t => t.trim().replace(/^#/, '')).filter(Boolean)
      : [];

    try {
      const newPost = await window.api.posts.create({
        title,
        excerpt,
        content,
        tags,
        is_published: isPublished
      });
      showToast('Post published successfully!', 'success');
      closeNewPostModal();
      e.target.reset();
      loadTags();
      showPostDetail(newPost.slug);
    } catch (err) {
      showToast(err.message, 'error');
    } finally {
      btn.disabled = false;
    }
  });

  // Listen to auth state changes from other tabs/windows
  window.addEventListener('auth:change', () => {
    updateAuthUI();
  });
});
