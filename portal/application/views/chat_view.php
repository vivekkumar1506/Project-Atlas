<?php defined('BASEPATH') OR exit('No direct script access allowed'); ?><!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="Project Atlas — Secure Market Research Report Copilot inside CodeIgniter 3 portal.">
    <title>Project Atlas — AI Market Research Report Copilot</title>
    <!-- Google Fonts Inter -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="<?php echo base_url('assets/css/portal.css'); ?>">
</head>
<body>

    <!-- Header Navigation -->
    <header class="portal-header">
        <div class="brand-section">
            <span class="brand-badge">ATLAS COPILOT</span>
            <h1 class="brand-title">Cognitive Market Research &amp; Consulting</h1>
        </div>

        <div class="client-switcher">
            <label for="clientSelect" style="font-size: 13px; color: #8b9bb4;">Active Client Session:</label>
            <select id="clientSelect" class="client-select" onchange="window.location.href='<?php echo base_url('index.php/auth/switch_client/'); ?>' + this.value">
                <option value="C-01" <?php echo ($client_id === 'C-01') ? 'selected' : ''; ?>>C-01: Northwind Utilities (R-101, R-103)</option>
                <option value="C-02" <?php echo ($client_id === 'C-02') ? 'selected' : ''; ?>>C-02: Blue Delta Infra (R-103 only)</option>
                <option value="C-03" <?php echo ($client_id === 'C-03') ? 'selected' : ''; ?>>C-03: Gamma Analytics (All Reports)</option>
            </select>
        </div>
    </header>

    <!-- Main Container -->
    <div class="portal-container">
        <!-- Sidebar -->
        <aside class="portal-sidebar">
            <div class="sidebar-section">
                <h2 class="sidebar-title">Client Account Context</h2>
                <div class="entitlement-card" style="margin-top: 8px;">
                    <strong><?php echo htmlspecialchars($client_name, ENT_QUOTES, 'UTF-8'); ?></strong>
                    <div style="margin-top: 6px; color: #8b9bb4; font-size: 12px;">ID: <?php echo htmlspecialchars($client_id, ENT_QUOTES, 'UTF-8'); ?></div>
                </div>
            </div>

            <div class="sidebar-section">
                <h2 class="sidebar-title">Purchased Entitlements</h2>
                <div class="entitlement-card" style="margin-top: 8px;">
                    <?php if ($client_id === 'C-01'): ?>
                        <span class="entitlement-pill pill-active">R-101 (Smart Water 2025)</span>
                        <span class="entitlement-pill pill-active">R-102 (Public Excerpt)</span>
                        <span class="entitlement-pill pill-active">R-103 (Purifiers 2025)</span>
                    <?php elseif ($client_id === 'C-02'): ?>
                        <span class="entitlement-pill pill-active">R-103 (Purifiers 2025)</span>
                        <span class="entitlement-pill pill-active">R-102 (Public Excerpt)</span>
                        <span class="entitlement-pill pill-upgrade">R-101 (Upgrade Required)</span>
                    <?php else: ?>
                        <span class="entitlement-pill pill-active">Full Catalog Access</span>
                    <?php endif; ?>
                </div>
            </div>

            <div class="sidebar-section" style="flex: 1; overflow-y: auto;">
                <h2 class="sidebar-title">Analyst Escalations</h2>
                <div id="escalationsList" style="margin-top: 8px; display: flex; flex-direction: column; gap: 8px;">
                    <?php if (!empty($escalations)): ?>
                        <?php foreach ($escalations as $esc): ?>
                            <div class="entitlement-card" style="border-left: 3px solid #ef4444; font-size: 12px;">
                                <strong>Ticket: <?php echo htmlspecialchars($esc['ticket_id'], ENT_QUOTES, 'UTF-8'); ?></strong>
                                <div style="color: #94a3b8; margin-top: 3px;"><?php echo htmlspecialchars($esc['reason'], ENT_QUOTES, 'UTF-8'); ?></div>
                                <div style="color: #64748b; font-size: 11px; margin-top: 4px;">Status: <span style="color: #f87171; text-transform: uppercase;"><?php echo htmlspecialchars($esc['status'], ENT_QUOTES, 'UTF-8'); ?></span></div>
                            </div>
                        <?php endforeach; ?>
                    <?php else: ?>
                        <div style="font-size: 12px; color: #64748b; padding: 8px;">No active escalation tickets for this client.</div>
                    <?php endif; ?>
                </div>
            </div>
        </aside>

        <!-- Chat Workspace -->
        <main class="chat-main">
            <!-- Messages Viewport -->
            <div class="messages-viewport" id="messagesViewport">
                <!-- Welcome Banner -->
                <div class="msg-row msg-assistant">
                    <div class="msg-bubble">
                        <strong>Project Atlas Report Copilot</strong><br>
                        Hello! I am your AI Market Research Copilot. You can ask questions regarding your entitled syndicated market reports.
                        All figures are strictly validated against verified sources, calculations follow deterministic financial formulas, and conflicting reports are explicitly reconciled without averaging.
                    </div>
                </div>

                <!-- Initial History Rendering -->
                <?php if (!empty($history)): ?>
                    <?php foreach ($history as $h): ?>
                        <div class="msg-row msg-<?php echo ($h['role'] === 'user') ? 'user' : 'assistant'; ?>">
                            <div class="msg-bubble">
                                <div style="white-space: pre-wrap;"><?php echo htmlspecialchars($h['content'], ENT_QUOTES, 'UTF-8'); ?></div>
                            </div>
                            <?php if ($h['role'] === 'assistant'): ?>
                                <div class="msg-footer">
                                    <span>Verified by Critic</span>
                                </div>
                            <?php endif; ?>
                        </div>
                    <?php endforeach; ?>
                <?php endif; ?>
            </div>

            <!-- Error Banner -->
            <div id="alertBanner" class="alert-banner" style="display: none; margin: 0 20px;">
                <span id="alertText">An error occurred while connecting to the Report Copilot.</span>
                <button type="button" id="retryBtn" class="btn-retry">Retry Question</button>
            </div>

            <!-- Loading Indicator -->
            <div id="loadingIndicator" style="display: none; padding: 6px 20px; font-size: 13px; color: #60a5fa;">
                ⚡ Consulting entitled report knowledge base and verifying citations...
            </div>

            <!-- Input Bar -->
            <div class="chat-input-bar">
                <!-- Hidden CSRF token -->
                <input type="hidden" name="<?php echo htmlspecialchars($csrf_token, ENT_QUOTES, 'UTF-8'); ?>" id="csrf_token" value="<?php echo htmlspecialchars($csrf_hash, ENT_QUOTES, 'UTF-8'); ?>">

                <div class="input-container">
                    <textarea id="chatInput" class="chat-textarea" placeholder="Ask a question about your market reports (e.g. Compare 2024 smart water meter estimates)..." rows="1" maxlength="2000"></textarea>
                    <button type="button" id="sendBtn" class="btn-send">Send</button>
                </div>
            </div>
        </main>
    </div>

    <!-- Frontend Script -->
    <script src="<?php echo base_url('assets/js/portal.js'); ?>"></script>
</body>
</html>
