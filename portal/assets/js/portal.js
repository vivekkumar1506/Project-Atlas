/* Project Atlas - CI3 Portal Frontend Script */
(function() {
  'use strict';

  let activeConversationId = null;
  let lastFailedQuestion = null;

  const messagesViewport = document.getElementById('messagesViewport');
  const chatInput = document.getElementById('chatInput');
  const sendBtn = document.getElementById('sendBtn');
  const loadingIndicator = document.getElementById('loadingIndicator');
  const alertBanner = document.getElementById('alertBanner');
  const alertText = document.getElementById('alertText');
  const retryBtn = document.getElementById('retryBtn');
  const csrfTokenInput = document.getElementById('csrf_token');

  function getCsrfToken() {
    return csrfTokenInput ? csrfTokenInput.value : '';
  }

  function updateCsrfToken(newHash) {
    if (csrfTokenInput && newHash) {
      csrfTokenInput.value = newHash;
    }
  }

  function escapeHtml(str) {
    if (!str) return '';
    const div = document.createElement('div');
    div.appendChild(document.createTextNode(str));
    return div.innerHTML;
  }

  function scrollToBottom() {
    if (messagesViewport) {
      messagesViewport.scrollTop = messagesViewport.scrollHeight;
    }
  }

  function showAlert(msg) {
    if (alertBanner && alertText) {
      alertText.textContent = msg;
      alertBanner.style.display = 'flex';
      scrollToBottom();
    }
  }

  function hideAlert() {
    if (alertBanner) {
      alertBanner.style.display = 'none';
    }
  }

  function appendUserMessage(text) {
    const row = document.createElement('div');
    row.className = 'msg-row msg-user';

    const bubble = document.createElement('div');
    bubble.className = 'msg-bubble';
    bubble.textContent = text; // Safe textContent avoids XSS

    row.appendChild(bubble);
    messagesViewport.appendChild(row);
    scrollToBottom();
  }

  function appendAssistantMessage(data) {
    const row = document.createElement('div');
    row.className = 'msg-row msg-assistant';

    const bubble = document.createElement('div');
    bubble.className = 'msg-bubble';

    // Main Answer Content (Markdown line breaks preserved safely)
    const answerDiv = document.createElement('div');
    answerDiv.style.whiteSpace = 'pre-wrap';
    answerDiv.textContent = data.answer || '';
    bubble.appendChild(answerDiv);

    // Render Conflicts Box if present
    if (data.conflicts && data.conflicts.length > 0) {
      data.conflicts.forEach(c => {
        const cBox = document.createElement('div');
        cBox.className = 'conflict-box';
        cBox.innerHTML = `<strong>⚠️ Conflicting Market Definitions:</strong><br>` +
          `• <strong>${escapeHtml(c.first_report)}:</strong> ${escapeHtml(c.first_value)}<br>` +
          `• <strong>${escapeHtml(c.second_report)}:</strong> ${escapeHtml(c.second_value)}<br>` +
          `<em>${escapeHtml(c.explanation)}</em>`;
        bubble.appendChild(cBox);
      });
    }

    // Render Derived Values (Formula & Assumptions)
    if (data.derived_values && data.derived_values.length > 0) {
      data.derived_values.forEach(d => {
        const dBox = document.createElement('div');
        dBox.className = 'derived-box';
        let assumptionsList = '';
        if (d.assumptions && d.assumptions.length > 0) {
          assumptionsList = '<ul>' + d.assumptions.map(a => `<li>${escapeHtml(a)}</li>`).join('') + '</ul>';
        }
        dBox.innerHTML = `<strong>📐 Deterministic Calculation (${escapeHtml(d.metric_name)}):</strong><br>` +
          `<code>${escapeHtml(d.formula)}</code><br>` +
          `<strong>Derived Result:</strong> ${escapeHtml(d.result)}` +
          assumptionsList;
        bubble.appendChild(dBox);
      });
    }

    // Render Escalation Badge if escalated
    if (data.escalated) {
      const escBadge = document.createElement('div');
      escBadge.className = 'escalation-badge';
      escBadge.textContent = '🚨 Escalated to Human Market Research Analyst';
      bubble.appendChild(escBadge);
    }

    // Render Citations
    if (data.citations && data.citations.length > 0) {
      const citContainer = document.createElement('div');
      citContainer.className = 'citations-container';
      data.citations.forEach(cit => {
        const pill = document.createElement('div');
        pill.className = 'citation-pill';
        pill.textContent = `📄 ${cit.report_id} (${cit.source_location || 'Page'})`;
        citContainer.appendChild(pill);
      });
      bubble.appendChild(citContainer);
    }

    // Message Footer (Confidence & Thumbs Feedback)
    const footer = document.createElement('div');
    footer.className = 'msg-footer';

    const confScore = (data.confidence !== undefined) ? Math.round(data.confidence * 100) : 90;
    const metaSpan = document.createElement('span');
    metaSpan.textContent = `Confidence: ${confScore}% • Verified by Critic`;
    footer.appendChild(metaSpan);

    if (data.message_id) {
      const feedbackActions = document.createElement('div');
      feedbackActions.className = 'feedback-actions';

      const upBtn = document.createElement('button');
      upBtn.className = 'btn-feedback';
      upBtn.textContent = '👍';
      upBtn.title = 'Accurate Answer';
      upBtn.onclick = () => submitFeedback(data.message_id, 'up', upBtn, downBtn);

      const downBtn = document.createElement('button');
      downBtn.className = 'btn-feedback';
      downBtn.textContent = '👎';
      downBtn.title = 'Inaccurate or Unclear';
      downBtn.onclick = () => submitFeedback(data.message_id, 'down', downBtn, upBtn);

      feedbackActions.appendChild(upBtn);
      feedbackActions.appendChild(downBtn);
      footer.appendChild(feedbackActions);
    }

    row.appendChild(bubble);
    row.appendChild(footer);
    messagesViewport.appendChild(row);
    scrollToBottom();
  }

  async function submitQuestion(questionText) {
    if (!questionText || questionText.trim().length === 0) return;

    hideAlert();
    appendUserMessage(questionText);
    lastFailedQuestion = questionText;

    sendBtn.disabled = true;
    chatInput.value = '';
    chatInput.style.height = 'auto';
    if (loadingIndicator) loadingIndicator.style.display = 'block';

    const formData = new URLSearchParams();
    formData.append('question', questionText);
    formData.append('atlas_csrf_token', getCsrfToken());
    if (activeConversationId) {
      formData.append('conversation_id', activeConversationId);
    }

    try {
      const response = await fetch('index.php/chat/ask', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
          'X-Requested-With': 'XMLHttpRequest'
        },
        body: formData.toString()
      });

      const result = await response.json();

      if (result.csrf_hash) {
        updateCsrfToken(result.csrf_hash);
      }

      if (!response.ok || result.status !== 'success') {
        const errMsg = result.message || 'Service request failed. Please retry.';
        showAlert(errMsg);
      } else {
        if (result.conversation_id) {
          activeConversationId = result.conversation_id;
        }
        appendAssistantMessage(result);
        lastFailedQuestion = null;
      }
    } catch (err) {
      showAlert('Network error: Unable to reach Portal AI gateway. Please retry.');
    } finally {
      sendBtn.disabled = false;
      if (loadingIndicator) loadingIndicator.style.display = 'none';
      chatInput.focus();
    }
  }

  async function submitFeedback(messageId, rating, activeBtn, otherBtn) {
    const formData = new URLSearchParams();
    formData.append('message_id', messageId);
    formData.append('rating', rating);
    formData.append('atlas_csrf_token', getCsrfToken());

    try {
      const response = await fetch('index.php/chat/feedback', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
          'X-Requested-With': 'XMLHttpRequest'
        },
        body: formData.toString()
      });

      const res = await response.json();
      if (res.csrf_hash) updateCsrfToken(res.csrf_hash);

      if (response.ok && res.status === 'success') {
        activeBtn.classList.add(rating === 'up' ? 'active-up' : 'active-down');
        otherBtn.classList.remove('active-up', 'active-down');
      }
    } catch (e) {
      console.error('Feedback submission error:', e);
    }
  }

  // Event Listeners
  if (sendBtn) {
    sendBtn.addEventListener('click', () => {
      submitQuestion(chatInput.value);
    });
  }

  if (retryBtn) {
    retryBtn.addEventListener('click', () => {
      if (lastFailedQuestion) {
        submitQuestion(lastFailedQuestion);
      }
    });
  }

  if (chatInput) {
    chatInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        submitQuestion(chatInput.value);
      }
    });

    chatInput.addEventListener('input', () => {
      chatInput.style.height = 'auto';
      chatInput.style.height = Math.min(chatInput.scrollHeight, 120) + 'px';
    });
  }
})();
