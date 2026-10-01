/**
 * XploreElite - Floating Tourism Intelligence Chatbot
 * Powered by Groq AI Inference
 */

(function () {
  // 1. Guard check: Never initialize on the login page
  const currentPath = window.location.pathname.toLowerCase();
  if (currentPath.includes('login.html') || currentPath.endsWith('/login')) {
    return;
  }

  // Configuration
  const GROQ_CONFIG = {
    apiKey: window.GROQ_API_KEY || localStorage.getItem('GROQ_API_KEY') || '',
    primaryModel: 'openai/gpt-oss-120b',
    fallbackModel: 'openai/gpt-oss-20b',
    directEndpoint: 'https://api.groq.com/openai/v1/chat/completions',
    backendEndpoint: '/api/chatbot'
  };

  const STORAGE_KEY = 'xplore_chatbot_history_v2';
  let chatHistory = [];
  let isAwaitingResponse = false;

  // 2. Initialize DOM elements
  function initChatbot() {
    // If widget already injected, prevent duplicates
    if (document.getElementById('xploreChatWidget')) return;

    // Load Chatbot CSS dynamically if not present
    if (!document.querySelector('link[href*="chatbot.css"]')) {
      const link = document.createElement('link');
      link.rel = 'stylesheet';
      // Determine relative path based on directory depth
      const isInsideTemplates = window.location.pathname.includes('/templates/');
      link.href = isInsideTemplates ? '../static/css/chatbot.css' : 'static/css/chatbot.css';
      document.head.appendChild(link);
    }

    // Floating Trigger Button
    const triggerBtn = document.createElement('button');
    triggerBtn.id = 'xploreChatTrigger';
    triggerBtn.className = 'xplore-chat-trigger';
    triggerBtn.setAttribute('aria-label', 'Open XploreAI Chatbot');
    triggerBtn.innerHTML = `
      <div class="chat-trigger-icon" id="chatTriggerIcon">
        <i class="fa-solid fa-robot"></i>
      </div>
      <div class="xplore-chat-pulse"></div>
    `;

    // Tooltip greeting
    const tooltip = document.createElement('div');
    tooltip.id = 'xploreChatTooltip';
    tooltip.className = 'xplore-chat-tooltip';
    tooltip.innerHTML = `
      <span>Ask <strong>XploreAI</strong></span>
      <i class="fa-solid fa-sparkles" style="color: #e11d48;"></i>
    `;

    // Chatbot Window
    const widget = document.createElement('div');
    widget.id = 'xploreChatWidget';
    widget.className = 'xplore-chat-widget';
    widget.innerHTML = `
      <!-- Header -->
      <div class="xplore-chat-header">
        <div class="xplore-chat-header-info">
          <div class="xplore-chat-avatar">
            <i class="fa-solid fa-robot"></i>
            <div class="xplore-chat-avatar-status"></div>
          </div>
          <div class="xplore-chat-title-group">
            <h3>XploreAI <span class="xplore-chat-badge">Copilot</span></h3>
            <p><i class="fa-solid fa-bolt" style="color: #f59e0b;"></i> Powered by Groq • Online</p>
          </div>
        </div>
        <div class="xplore-chat-controls">
          <button class="xplore-chat-control-btn" id="xploreClearChatBtn" title="Clear Conversation">
            <i class="fa-solid fa-rotate-right"></i>
          </button>
          <button class="xplore-chat-control-btn" id="xploreCloseChatBtn" title="Close Chat">
            <i class="fa-solid fa-xmark"></i>
          </button>
        </div>
      </div>

      <!-- Quick Suggestion Chips -->
      <div class="xplore-chat-suggestions" id="xploreSuggestions">
        <button class="xplore-suggestion-chip" data-query="Summarize tourism footfall & gross revenue for 2025.">
          <i class="fa-solid fa-chart-line"></i> Summary
        </button>
        <button class="xplore-suggestion-chip" data-query="Which season has the peak visitor turnout and why?">
          <i class="fa-solid fa-calendar-check"></i> Peak Season
        </button>
        <button class="xplore-suggestion-chip" data-query="How can we maximize revenue yield per visitor across destinations?">
          <i class="fa-solid fa-lightbulb"></i> Revenue Yield
        </button>
        <button class="xplore-suggestion-chip" data-query="What tourism features and reports can I analyze here?">
          <i class="fa-solid fa-compass"></i> Platform Guide
        </button>
      </div>

      <!-- Messages Body -->
      <div class="xplore-chat-messages" id="xploreChatMessages">
        <!-- Welcome Card -->
        <div class="xplore-chat-welcome" id="xploreWelcomeCard">
          <h4><i class="fa-solid fa-wand-magic-sparkles"></i> Welcome to XploreAI Copilot</h4>
          <p>I can help you analyze visitor trends, revenue forecasts, seasonal peaks, and tourism destination insights.</p>
          <div class="xplore-welcome-features">
            <span>📈 Footfall Analysis</span>
            <span>💰 Revenue Yields</span>
            <span>🔮 Predictions</span>
            <span>📍 Destinations</span>
          </div>
        </div>
      </div>

      <!-- Input Bar -->
      <div class="xplore-chat-footer">
        <div class="xplore-chat-input-bar">
          <input 
            type="text" 
            class="xplore-chat-input" 
            id="xploreChatInput" 
            placeholder="Ask about tourism trends, data, or reports..." 
            autocomplete="off"
          />
          <button class="xplore-chat-send-btn" id="xploreChatSendBtn" title="Send Message">
            <i class="fa-solid fa-arrow-up"></i>
          </button>
        </div>
        <div class="xplore-chat-meta-bar">
          <span><i class="fa-solid fa-bolt"></i> Ultra-Fast Groq Inference</span>
          <span>Press Enter to send</span>
        </div>
      </div>
    `;

    document.body.appendChild(triggerBtn);
    document.body.appendChild(tooltip);
    document.body.appendChild(widget);

    // Load persisted chat history
    loadSavedHistory();

    // Attach Event Listeners
    setupEventListeners(triggerBtn, tooltip, widget);
  }

  // 3. Load & Save History
  function loadSavedHistory() {
    try {
      const saved = sessionStorage.getItem(STORAGE_KEY);
      if (saved) {
        chatHistory = JSON.parse(saved);
        if (Array.isArray(chatHistory) && chatHistory.length > 0) {
          // Hide welcome card if history exists
          const welcome = document.getElementById('xploreWelcomeCard');
          if (welcome) welcome.style.display = 'none';

          chatHistory.forEach(msg => {
            renderMessage(msg.role, msg.content, msg.time, false);
          });
        }
      }
    } catch (e) {
      chatHistory = [];
    }
  }

  function saveHistory() {
    try {
      sessionStorage.setItem(STORAGE_KEY, JSON.stringify(chatHistory));
    } catch (e) {
      console.warn('Unable to save chat history to sessionStorage', e);
    }
  }

  // 4. Formatting helper: Simple, safe markdown parser
  function formatMarkdown(text) {
    if (!text) return '';
    let html = text
      // Escape angle brackets
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      // Bold **text**
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      // Italic *text*
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      // Code `text`
      .replace(/`([^`]+)`/g, '<code>$1</code>')
      // Numbered items or bullet lines
      .replace(/^\s*[\-\*]\s+(.*)$/gm, '<li>$1</li>')
      .replace(/^\s*(\d+)\.\s+(.*)$/gm, '<li><strong>$1.</strong> $2</li>');

    // Wrap contiguous list items in <ul>
    html = html.replace(/(<li>[\s\S]*?<\/li>)/g, '<ul>$1</ul>');
    // Remove duplicate nested uls if regex matched multiple
    html = html.replace(/<\/ul>\s*<ul>/g, '');

    // Paragraph splits
    const paras = html.split(/\n{2,}/);
    if (paras.length > 1) {
      html = paras.map(p => {
        if (p.startsWith('<ul>') || p.startsWith('<li>')) return p;
        return `<p>${p.replace(/\n/g, '<br>')}</p>`;
      }).join('');
    } else {
      html = html.replace(/\n/g, '<br>');
    }

    return html;
  }

  // 5. Render Message in DOM
  function renderMessage(role, text, timestamp = null, animate = true) {
    const container = document.getElementById('xploreChatMessages');
    if (!container) return;

    const timeStr = timestamp || new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

    const msgGroup = document.createElement('div');
    msgGroup.className = `xplore-msg-group ${role === 'user' ? 'user' : 'bot'}`;
    if (!animate) msgGroup.style.animation = 'none';

    if (role === 'assistant' || role === 'bot') {
      msgGroup.innerHTML = `
        <div class="xplore-msg-avatar">
          <i class="fa-solid fa-robot"></i>
        </div>
        <div class="xplore-msg-content-wrap">
          <div class="xplore-msg-bubble">${formatMarkdown(text)}</div>
          <div class="xplore-msg-time">${timeStr}</div>
        </div>
      `;
    } else {
      msgGroup.innerHTML = `
        <div class="xplore-msg-content-wrap">
          <div class="xplore-msg-bubble">${formatMarkdown(text)}</div>
          <div class="xplore-msg-time">${timeStr}</div>
        </div>
      `;
    }

    container.appendChild(msgGroup);
    container.scrollTop = container.scrollHeight;
  }

  // 6. Show / Hide Typing Indicator
  function showTypingIndicator() {
    const container = document.getElementById('xploreChatMessages');
    if (!container) return;

    removeTypingIndicator();

    const typing = document.createElement('div');
    typing.id = 'xploreTypingIndicator';
    typing.className = 'xplore-msg-group bot';
    typing.innerHTML = `
      <div class="xplore-msg-avatar">
        <i class="fa-solid fa-robot"></i>
      </div>
      <div class="xplore-msg-content-wrap">
        <div class="xplore-typing-bubble">
          <div class="xplore-typing-dot"></div>
          <div class="xplore-typing-dot"></div>
          <div class="xplore-typing-dot"></div>
        </div>
      </div>
    `;
    container.appendChild(typing);
    container.scrollTop = container.scrollHeight;
  }

  function removeTypingIndicator() {
    const existing = document.getElementById('xploreTypingIndicator');
    if (existing) existing.remove();
  }

  // 7. Send Query to AI (Backend -> Groq Fallback)
  async function queryAI(userText) {
    const pageName = window.location.pathname.split('/').pop() || 'dashboard.html';

    // 1st attempt: Call Flask backend endpoint
    try {
      const response = await fetch(GROQ_CONFIG.backendEndpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: userText,
          history: chatHistory.slice(-6),
          page: pageName
        })
      });

      if (response.ok) {
        const data = await response.json();
        if (data.success && data.reply) {
          return data.reply;
        }
      }
    } catch (backendErr) {
      console.warn('Backend chatbot endpoint unavailable, falling back directly to Groq API:', backendErr);
    }

    // 2nd attempt: Call Groq API directly from browser
    const systemPrompt = `You are XploreAI, the intelligent assistant for the XploreElite Tourism Footfall & Revenue Analytics Platform.
The user is viewing the page: ${pageName}.
Help them with tourism trends, visitor footfall calculations, revenue forecasts, peak season planning, and navigation.
Keep answers concise, structured, professional, and friendly with formatting (bolding and bullet points).`;

    const messages = [
      { role: 'system', content: systemPrompt }
    ];

    chatHistory.slice(-6).forEach(m => {
      messages.push({ role: m.role === 'assistant' ? 'assistant' : 'user', content: m.content });
    });
    messages.push({ role: 'user', content: userText });

    const modelsToTry = [GROQ_CONFIG.primaryModel, GROQ_CONFIG.fallbackModel, 'qwen/qwen3.8-27b'];

    for (const model of modelsToTry) {
      try {
        const directRes = await fetch(GROQ_CONFIG.directEndpoint, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${GROQ_CONFIG.apiKey}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            model: model,
            messages: messages,
            temperature: 0.7,
            max_tokens: 1000
          })
        });

        if (directRes.ok) {
          const directData = await directRes.json();
          if (directData.choices && directData.choices[0] && directData.choices[0].message) {
            return directData.choices[0].message.content;
          }
        }
      } catch (err) {
        console.warn(`Groq model ${model} failed, trying fallback:`, err);
      }
    }

    throw new Error('All AI endpoints are currently busy or unavailable. Please check your internet connection and try again.');
  }

  // 8. Handle Send Message Flow
  async function handleSend() {
    const input = document.getElementById('xploreChatInput');
    const sendBtn = document.getElementById('xploreChatSendBtn');
    if (!input || isAwaitingResponse) return;

    const text = input.value.trim();
    if (!text) return;

    // Hide welcome card
    const welcome = document.getElementById('xploreWelcomeCard');
    if (welcome) welcome.style.display = 'none';

    // Clear input & disable
    input.value = '';
    isAwaitingResponse = true;
    if (sendBtn) sendBtn.disabled = true;

    // Record user message
    const nowTime = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    renderMessage('user', text, nowTime);
    chatHistory.push({ role: 'user', content: text, time: nowTime });
    saveHistory();

    // Show typing dots
    showTypingIndicator();

    try {
      const reply = await queryAI(text);
      removeTypingIndicator();
      const replyTime = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
      renderMessage('assistant', reply, replyTime);
      chatHistory.push({ role: 'assistant', content: reply, time: replyTime });
      saveHistory();
    } catch (error) {
      removeTypingIndicator();
      const errorMsg = `⚠️ **Notice:** ${error.message || 'Unable to connect to AI server.'}`;
      renderMessage('assistant', errorMsg);
    } finally {
      isAwaitingResponse = false;
      if (sendBtn) sendBtn.disabled = false;
      input.focus();
    }
  }

  // 9. Attach Event Listeners
  function setupEventListeners(triggerBtn, tooltip, widget) {
    const icon = document.getElementById('chatTriggerIcon');
    const closeBtn = document.getElementById('xploreCloseChatBtn');
    const clearBtn = document.getElementById('xploreClearChatBtn');
    const input = document.getElementById('xploreChatInput');
    const sendBtn = document.getElementById('xploreChatSendBtn');
    const suggestions = document.getElementById('xploreSuggestions');

    function toggleChat(forceOpen = null) {
      const shouldOpen = forceOpen !== null ? forceOpen : !widget.classList.contains('active');
      if (shouldOpen) {
        widget.classList.add('active');
        triggerBtn.classList.add('active');
        tooltip.classList.add('hide');
        if (icon) icon.innerHTML = '<i class="fa-solid fa-chevron-down"></i>';
        setTimeout(() => input && input.focus(), 300);
      } else {
        widget.classList.remove('active');
        triggerBtn.classList.remove('active');
        if (icon) icon.innerHTML = '<i class="fa-solid fa-robot"></i>';
      }
    }

    triggerBtn.addEventListener('click', () => toggleChat());
    tooltip.addEventListener('click', () => toggleChat(true));
    if (closeBtn) closeBtn.addEventListener('click', () => toggleChat(false));

    // Clear Chat
    if (clearBtn) {
      clearBtn.addEventListener('click', () => {
        if (confirm('Clear current chat conversation?')) {
          chatHistory = [];
          sessionStorage.removeItem(STORAGE_KEY);
          const messages = document.getElementById('xploreChatMessages');
          if (messages) {
            messages.innerHTML = `
              <div class="xplore-chat-welcome" id="xploreWelcomeCard">
                <h4><i class="fa-solid fa-wand-magic-sparkles"></i> Welcome to XploreAI Copilot</h4>
                <p>Conversation cleared. Ask any question about tourism footfall, revenue, or trends!</p>
                <div class="xplore-welcome-features">
                  <span>📈 Footfall Analysis</span>
                  <span>💰 Revenue Yields</span>
                  <span>🔮 Predictions</span>
                </div>
              </div>
            `;
          }
        }
      });
    }

    // Send button & Enter key
    if (sendBtn) sendBtn.addEventListener('click', handleSend);
    if (input) {
      input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
          e.preventDefault();
          handleSend();
        }
      });
    }

    // Suggestion chips
    if (suggestions) {
      suggestions.addEventListener('click', (e) => {
        const chip = e.target.closest('.xplore-suggestion-chip');
        if (chip && chip.dataset.query) {
          input.value = chip.dataset.query;
          handleSend();
        }
      });
    }

    // Auto-dismiss tooltip after 8 seconds if not clicked
    setTimeout(() => {
      tooltip.classList.add('hide');
    }, 8000);
  }

  // 10. Bootstrap once DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initChatbot);
  } else {
    initChatbot();
  }
})();
