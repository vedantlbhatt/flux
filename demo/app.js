(function () {
  const $ = (id) => document.getElementById(id);

  function baseUrl() {
    return (($('baseUrl')?.value || '').trim() || 'http://localhost:8000').replace(/\/$/, '');
  }

  async function api(path, options = {}) {
    const url = baseUrl() + path;
    const res = await fetch(url, {
      ...options,
      headers: { 'Content-Type': 'application/json', ...options.headers },
    });
    const text = await res.text();
    if (res.status === 204) return null;
    let data;
    try {
      data = text ? JSON.parse(text) : null;
    } catch {
      throw new Error(res.ok ? text : `HTTP ${res.status}: ${text}`);
    }
    if (!res.ok) throw new Error(data?.error || data?.code || `HTTP ${res.status}`);
    return data;
  }

  // --- Health ---
  async function checkHealth() {
    const el = $('healthStatus');
    el.textContent = 'Checking…';
    el.className = 'health-status';
    try {
      const d = await api('/health');
      el.textContent = `Tavily: ${d.tavily_ready ? '✓' : '✗'}  Cohere: ${d.cohere_ready ? '✓' : '✗'}`;
      el.className = 'health-status ok';
    } catch (e) {
      el.textContent = e.message || 'Failed';
      el.className = 'health-status err';
    }
  }

  $('checkHealth')?.addEventListener('click', checkHealth);

  // --- Conversations state ---
  let currentConvId = null;
  let conversations = [];

  function renderConversationList() {
    const list = $('conversationList');
    list.innerHTML = conversations
      .map((c) => {
        const title = `Chat ${c.id.slice(0, 8)}…`;
        const active = c.id === currentConvId ? ' active' : '';
        return `<li class="${active}" data-id="${c.id}">
          <span class="conv-title">${title}</span>
          <button type="button" class="conv-delete" data-id="${c.id}" aria-label="Delete">🗑</button>
        </li>`;
      })
      .join('');

    list.querySelectorAll('li').forEach((li) => {
      const id = li.dataset.id;
      li.addEventListener('click', (e) => {
        if (!e.target.classList.contains('conv-delete')) selectConversation(id);
      });
    });
    list.querySelectorAll('.conv-delete').forEach((btn) => {
      btn.addEventListener('click', (e) => {
        e.stopPropagation();
        deleteConversation(btn.dataset.id);
      });
    });
  }

  async function loadConversations() {
    try {
      const data = await api('/conversations?page=1&page_size=50');
      conversations = data.conversations || [];
      renderConversationList();
    } catch (e) {
      console.error('Load conversations:', e);
      conversations = [];
      renderConversationList();
    }
  }

  async function createConversation() {
    try {
      const conv = await api('/conversations', { method: 'POST' });
      conversations = [{ id: conv.id, created_at: conv.created_at, message_count: 0 }, ...conversations];
      renderConversationList();
      selectConversation(conv.id);
    } catch (e) {
      alert('Failed to create conversation: ' + e.message);
    }
  }

  async function deleteConversation(id) {
    try {
      await api(`/conversations/${id}`, { method: 'DELETE' });
      conversations = conversations.filter((c) => c.id !== id);
      if (currentConvId === id) {
        currentConvId = null;
        showPlaceholder();
      }
      renderConversationList();
    } catch (e) {
      alert('Failed to delete: ' + e.message);
    }
  }

  function showPlaceholder() {
    $('chatPlaceholder').style.display = 'flex';
    $('chatMessages').style.display = 'none';
    $('chatInputArea').style.display = 'none';
    $('chatMessages').innerHTML = '';
  }

  function showChat() {
    $('chatPlaceholder').style.display = 'none';
    $('chatMessages').style.display = 'flex';
    $('chatInputArea').style.display = 'flex';
  }

  function renderMessage(msg) {
    const div = document.createElement('div');
    div.className = 'message user';
    div.innerHTML = `
      <span class="message-role">You</span>
      <div class="message-content">${escapeHtml(msg.query || '')}</div>
    `;
    $('chatMessages').appendChild(div);

    if (msg.answer != null || msg.error) {
      const adiv = document.createElement('div');
      adiv.className = 'message assistant';
      let meta = '';
      if (msg.citations && msg.citations.length) {
        meta = `<ul class="citations-list">${msg.citations.map((c) => `<li><a href="${escapeHtml(c.url)}" target="_blank" rel="noopener">${escapeHtml(c.title || c.url)}</a></li>`).join('')}</ul>`;
      }
      adiv.innerHTML = `
        <span class="message-role">Flux</span>
        <div class="message-content">${msg.error ? `Error: ${escapeHtml(msg.error)}` : escapeHtml(msg.answer || '')}</div>
        ${meta ? `<div class="message-meta">Sources: ${meta}</div>` : ''}
      `;
      $('chatMessages').appendChild(adiv);
    }
  }

  async function selectConversation(id) {
    currentConvId = id;
    renderConversationList();
    showChat();
    $('chatMessages').innerHTML = '<div class="loading">Loading…</div>';
    try {
      const conv = await api(`/conversations/${id}`);
      $('chatMessages').innerHTML = '';
      (conv.messages || []).forEach(renderMessage);
    } catch (e) {
      $('chatMessages').innerHTML = `<div class="message assistant"><div class="message-content">Failed to load: ${escapeHtml(e.message)}</div></div>`;
    }
  }

  async function sendMessage() {
    const input = $('messageInput');
    const query = (input?.value || '').trim();
    if (!query || !currentConvId) return;

    const loadingDiv = document.createElement('div');
    loadingDiv.className = 'message user';
    loadingDiv.innerHTML = `<span class="message-role">You</span><div class="message-content">${escapeHtml(query)}</div>`;
    $('chatMessages').appendChild(loadingDiv);

    const loadingAssistant = document.createElement('div');
    loadingAssistant.className = 'message assistant loading';
    loadingAssistant.textContent = 'Searching and synthesizing…';
    $('chatMessages').appendChild(loadingAssistant);
    input.value = '';

    try {
      const msg = await api(`/conversations/${currentConvId}/messages`, {
        method: 'POST',
        body: JSON.stringify({ query }),
      });
      loadingAssistant.remove();
      renderMessage({ query, answer: msg.answer, citations: msg.citations, error: msg.error });
      loadConversations();
    } catch (e) {
      loadingAssistant.textContent = 'Error: ' + e.message;
      loadingAssistant.classList.remove('loading');
      loadingAssistant.classList.add('message', 'assistant');
    }
  }

  $('newConversation')?.addEventListener('click', createConversation);
  $('sendMessage')?.addEventListener('click', sendMessage);
  $('messageInput')?.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });

  function escapeHtml(s) {
    const div = document.createElement('div');
    div.textContent = s;
    return div.innerHTML;
  }

  // --- Modals: Search, Answer, Contents ---
  function openModal(panelId, title) {
    $('modalSearch').style.display = panelId === 'modalSearch' ? 'flex' : 'none';
    $('modalAnswer').style.display = panelId === 'modalAnswer' ? 'flex' : 'none';
    $('modalContents').style.display = panelId === 'modalContents' ? 'flex' : 'none';
    $('modalTitle').textContent = title;
    $('modalOverlay').style.display = 'flex';
  }

  function closeModal() {
    $('modalOverlay').style.display = 'none';
  }

  $('closeModal')?.addEventListener('click', closeModal);
  $('modalOverlay')?.addEventListener('click', (e) => {
    if (e.target === $('modalOverlay')) closeModal();
  });

  $('openSearch')?.addEventListener('click', () => openModal('modalSearch', 'GET /search'));
  $('openAnswer')?.addEventListener('click', () => openModal('modalAnswer', 'GET /answer'));
  $('openContents')?.addEventListener('click', () => openModal('modalContents', 'GET /contents'));

  function setResult(elId, data, isError) {
    const el = $(elId);
    el.textContent = typeof data === 'string' ? data : JSON.stringify(data, null, 2);
    el.className = 'api-result' + (isError ? ' error' : '') + (!data ? ' empty' : '');
  }

  $('runSearch')?.addEventListener('click', async () => {
    const q = ($('searchQuery')?.value || '').trim();
    const limit = Math.max(1, Math.min(20, parseInt($('searchLimit')?.value || '5', 10) || 5));
    if (!q) {
      setResult('searchResult', 'Enter a query.', true);
      return;
    }
    setResult('searchResult', 'Loading…');
    try {
      const data = await api(`/search?q=${encodeURIComponent(q)}&limit=${limit}`);
      setResult('searchResult', data);
    } catch (e) {
      setResult('searchResult', e.message, true);
    }
  });

  $('runAnswer')?.addEventListener('click', async () => {
    const q = ($('answerQuery')?.value || '').trim();
    if (!q) {
      setResult('answerResult', 'Enter a question.', true);
      return;
    }
    setResult('answerResult', 'Loading…');
    try {
      const data = await api(`/answer?q=${encodeURIComponent(q)}`);
      setResult('answerResult', data);
    } catch (e) {
      setResult('answerResult', e.message, true);
    }
  });

  $('runContents')?.addEventListener('click', async () => {
    const urls = ($('contentsUrls')?.value || '')
      .split(',')
      .map((u) => u.trim())
      .filter(Boolean);
    if (!urls.length) {
      setResult('contentsResult', 'Enter at least one URL.', true);
      return;
    }
    setResult('contentsResult', 'Loading…');
    try {
      const data = await api(`/contents?urls=${urls.map(encodeURIComponent).join(',')}`);
      setResult('contentsResult', data);
    } catch (e) {
      setResult('contentsResult', e.message, true);
    }
  });

  // --- Init ---
  checkHealth();
  loadConversations();
})();
