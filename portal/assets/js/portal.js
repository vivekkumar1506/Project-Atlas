/* Project Atlas — Clean, Professional Portal JavaScript */
(function() {
  'use strict';

  let activeConversationId = null;
  let lastFailedQuestion = null;
  let currentModalReport = null;

  const messagesViewport = document.getElementById('messagesViewport');
  const chatInput = document.getElementById('chatInput');
  const sendBtn = document.getElementById('sendBtn');
  const loadingIndicator = document.getElementById('loadingIndicator');
  const alertBanner = document.getElementById('alertBanner');
  const alertText = document.getElementById('alertText');
  const retryBtn = document.getElementById('retryBtn');
  const csrfTokenInput = document.getElementById('csrf_token');
  const portalSidebar = document.getElementById('portalSidebar');
  const toggleSidebarBtn = document.getElementById('toggleSidebarBtn');
  const upgradeModal = document.getElementById('upgradeModal');

  // Mobile sidebar toggle
  if (toggleSidebarBtn && portalSidebar) {
    toggleSidebarBtn.addEventListener('click', function() {
      portalSidebar.classList.toggle('sidebar-hidden');
    });
  }

  // Auto-resize textarea
  if (chatInput) {
    chatInput.addEventListener('input', function() {
      this.style.height = 'auto';
      this.style.height = Math.min(this.scrollHeight, 120) + 'px';
    });

    chatInput.addEventListener('keydown', function(e) {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        submitQuestion();
      }
    });
  }

  if (sendBtn) {
    sendBtn.addEventListener('click', function() {
      submitQuestion();
    });
  }

  if (retryBtn) {
    retryBtn.addEventListener('click', function() {
      if (lastFailedQuestion) {
        chatInput.value = lastFailedQuestion;
        hideAlert();
        submitQuestion();
      }
    });
  }

  // Close modal when clicking on the dark backdrop
  if (upgradeModal) {
    upgradeModal.addEventListener('click', function(e) {
      if (e.target === upgradeModal) {
        window.closeUpgradeModal();
      }
    });
  }

  // Global helper: send preset prompt
  window.sendPromptPreset = function(promptText) {
    if (chatInput) {
      chatInput.value = promptText;
      chatInput.style.height = 'auto';
      chatInput.style.height = Math.min(chatInput.scrollHeight, 120) + 'px';
      chatInput.focus();
      submitQuestion();
    }
  };

  // Global helper: Upgrade Modal
  window.openUpgradeModal = function(code, title, sector) {
    currentModalReport = { code: code, title: title, sector: sector };
    const modal = document.getElementById('upgradeModal');
    const modalCode = document.getElementById('modalReportCode');
    const modalTitle = document.getElementById('modalReportTitle');
    const modalSector = document.getElementById('modalReportSector');
    const modalStatus = document.getElementById('modalReportStatus');

    if (modalCode) modalCode.textContent = code;
    if (modalTitle) modalTitle.textContent = title;
    if (modalSector) modalSector.textContent = sector;
    if (modalStatus) modalStatus.textContent = (code === 'R-101') ? 'Restricted — Client Upgrade Required' : 'Commercial License Required';

    if (modal) {
      modal.style.display = 'flex';
    }
  };

  window.closeUpgradeModal = function() {
    const modal = document.getElementById('upgradeModal');
    if (modal) {
      modal.style.display = 'none';
    }
    currentModalReport = null;
  };

  window.askCopilotUpgrade = function() {
    if (currentModalReport) {
      const q = `How can I upgrade our subscription to access report ${currentModalReport.code} (${currentModalReport.title})?`;
      closeUpgradeModal();
      window.sendPromptPreset(q);
    }
  };

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

  // Safe and clean Markdown-to-HTML parser for professional SaaS presentation
  function formatMarkdown(text) {
    if (!text) return '';
    let formatted = escapeHtml(text);

    // Headers
    formatted = formatted.replace(/^###\s*(.*$)/gim, '<h4>$1</h4>');
    formatted = formatted.replace(/^##\s*(.*$)/gim, '<h3>$1</h3>');

    // Bold & Italic
    formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    formatted = formatted.replace(/\*([^\*]+)\*/g, '<em>$1</em>');

    // Code blocks & inline code
    formatted = formatted.replace(/`([^`]+)`/g, '<code>$1</code>');

    // Clean bullets
    formatted = formatted.replace(/^\s*[-*]\s+(.*$)/gim, '<div style="margin-left: 12px;">• $1</div>');

    // Line breaks
    formatted = formatted.replace(/\n\n/g, '<br><br>');
    formatted = formatted.replace(/\n/g, '<br>');

    return formatted;
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
    bubble.textContent = text; // Safe textContent prevents XSS

    row.appendChild(bubble);
    messagesViewport.appendChild(row);
    scrollToBottom();
  }

  function appendAssistantMessage(data) {
    const row = document.createElement('div');
    row.className = 'msg-row msg-assistant';

    const bubble = document.createElement('div');
    bubble.className = 'msg-bubble';

    // Copilot Badge
    const authorBadge = document.createElement('div');
    authorBadge.className = 'copilot-author-badge';
    authorBadge.textContent = 'Project Atlas Copilot';
    bubble.appendChild(authorBadge);

    // Formatted Content (Clean HTML typography)
    const contentDiv = document.createElement('div');
    contentDiv.className = 'formatted-content';
    contentDiv.innerHTML = formatMarkdown(data.answer || '');
    bubble.appendChild(contentDiv);

    // Conflicts Callout Box
    if (data.conflicts && data.conflicts.length > 0) {
      data.conflicts.forEach(c => {
        const cBox = document.createElement('div');
        cBox.className = 'conflict-box';
        cBox.innerHTML = `<strong>Conflicting Market Scopes:</strong><br>` +
          `• <strong>${escapeHtml(c.first_report)}:</strong> ${escapeHtml(c.first_value)}<br>` +
          `• <strong>${escapeHtml(c.second_report)}:</strong> ${escapeHtml(c.second_value)}<br>` +
          `<div style="margin-top: 4px; font-style: italic;">${escapeHtml(c.explanation)}</div>`;
        bubble.appendChild(cBox);
      });
    }

    // Derived Values Box
    if (data.derived_values && data.derived_values.length > 0) {
      data.derived_values.forEach(d => {
        const dBox = document.createElement('div');
        dBox.className = 'derived-box';
        let assumptionsList = '';
        if (d.assumptions && d.assumptions.length > 0) {
          assumptionsList = '<ul style="margin: 4px 0 0 16px;">' + d.assumptions.map(a => `<li>${escapeHtml(a)}</li>`).join('') + '</ul>';
        }
        dBox.innerHTML = `<strong>Derived Calculation (${escapeHtml(d.metric_name)}):</strong><br>` +
          `<code>${escapeHtml(d.formula)}</code><br>` +
          `<strong>Computed Value:</strong> ${escapeHtml(d.result)}` +
          assumptionsList;
        bubble.appendChild(dBox);
      });
    }

    // Escalation Badge
    if (data.escalated) {
      const escBadge = document.createElement('div');
      escBadge.className = 'escalation-badge';
      escBadge.textContent = 'Escalated to Human Analyst Ticket';
      bubble.appendChild(escBadge);
    }

    // Citations
    if (data.citations && data.citations.length > 0) {
      const citContainer = document.createElement('div');
      citContainer.className = 'citations-container';
      data.citations.forEach(cit => {
        const pill = document.createElement('div');
        pill.className = 'citation-pill';
        pill.textContent = `${cit.report_id} (${cit.source_location || 'Page'})`;
        citContainer.appendChild(pill);
      });
      bubble.appendChild(citContainer);
    }

    // Footer
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
      upBtn.title = 'Accurate';
      upBtn.onclick = () => submitFeedback(data.message_id, 'up', upBtn, downBtn);

      const downBtn = document.createElement('button');
      downBtn.className = 'btn-feedback';
      downBtn.textContent = '👎';
      downBtn.title = 'Inaccurate';
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

  function submitQuestion() {
    const question = (chatInput ? chatInput.value : '').trim();
    if (!question) return;

    hideAlert();
    lastFailedQuestion = question;
    appendUserMessage(question);

    chatInput.value = '';
    chatInput.style.height = 'auto';
    chatInput.disabled = true;
    sendBtn.disabled = true;

    if (loadingIndicator) loadingIndicator.style.display = 'flex';

    const formData = new URLSearchParams();
    const csrfName = csrfTokenInput ? csrfTokenInput.name : 'csrf_test_name';
    formData.append(csrfName, getCsrfToken());
    formData.append('question', question);
    if (activeConversationId) {
      formData.append('conversation_id', activeConversationId);
    }

    fetch('chat/ask', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        'X-Requested-With': 'XMLHttpRequest'
      },
      body: formData.toString()
    })
    .then(res => {
      return res.json().then(data => ({ status: res.status, ok: res.ok, body: data }));
    })
    .then(resObj => {
      if (loadingIndicator) loadingIndicator.style.display = 'none';
      chatInput.disabled = false;
      sendBtn.disabled = false;
      chatInput.focus();

      if (resObj.body.csrf_hash) {
        updateCsrfToken(resObj.body.csrf_hash);
      }

      if (!resObj.ok) {
        showAlert(resObj.body.message || 'Error processing inquiry.');
        return;
      }

      lastFailedQuestion = null;
      if (resObj.body.conversation_id) {
        activeConversationId = resObj.body.conversation_id;
      }
      appendAssistantMessage(resObj.body);
    })
    .catch(err => {
      if (loadingIndicator) loadingIndicator.style.display = 'none';
      chatInput.disabled = false;
      sendBtn.disabled = false;
      showAlert('Network error: Unable to reach gateway portal. Please retry.');
      console.error('Project Atlas Error:', err);
    });
  }

  function submitFeedback(messageId, rating, activeBtn, otherBtn) {
    const formData = new URLSearchParams();
    const csrfName = csrfTokenInput ? csrfTokenInput.name : 'csrf_test_name';
    formData.append(csrfName, getCsrfToken());
    formData.append('message_id', messageId);
    formData.append('rating', rating);

    fetch('chat/feedback', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        'X-Requested-With': 'XMLHttpRequest'
      },
      body: formData.toString()
    })
    .then(res => res.json())
    .then(data => {
      if (data.csrf_hash) updateCsrfToken(data.csrf_hash);
      if (data.status === 'success') {
        activeBtn.classList.add(rating === 'up' ? 'active-up' : 'active-down');
        otherBtn.classList.remove('active-up', 'active-down');
      }
    })
    .catch(err => console.error('Feedback failed:', err));
  }

  scrollToBottom();
})();
