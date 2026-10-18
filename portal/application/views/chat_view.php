<?php defined('BASEPATH') OR exit('No direct script access allowed'); ?><!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="Project Atlas — Secure Market Research Report Copilot">
    <title>Project Atlas — AI Market Research Report Copilot</title>
    <!-- Clean Google Font Inter -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="<?php echo base_url('assets/css/portal.css'); ?>">
</head>
<body>

    <!-- Header Navigation -->
    <header class="portal-header">
        <div class="brand-section">
            <span class="brand-badge">Atlas Copilot</span>
            <div>
                <h1 class="brand-title">Cognitive Market Research</h1>
                <div class="brand-subtitle">Enterprise Syndicated Intelligence &amp; Access-Aware RAG</div>
            </div>
        </div>

        <div class="header-controls">
            <div class="client-switcher-wrap">
                <label for="clientSelect">Active Client:</label>
                <select id="clientSelect" class="client-select" onchange="window.location.href='<?php echo base_url('index.php/auth/switch_client/'); ?>' + this.value">
                    <option value="C-01" <?php echo ($client_id === 'C-01') ? 'selected' : ''; ?>>C-01: Northwind Utilities (R-101, R-103)</option>
                    <option value="C-02" <?php echo ($client_id === 'C-02') ? 'selected' : ''; ?>>C-02: Blue Delta Infra (R-103 only)</option>
                    <option value="C-03" <?php echo ($client_id === 'C-03') ? 'selected' : ''; ?>>C-03: Gamma Analytics (Full Enterprise &amp; Upgrades)</option>
                </select>
            </div>
            <button type="button" id="toggleSidebarBtn" class="btn-mobile-sidebar">Reports &amp; Status</button>
        </div>
    </header>

    <!-- Main Container -->
    <div class="portal-container">
        <!-- Sidebar -->
        <aside class="portal-sidebar" id="portalSidebar">
            <!-- Client Account Context Card -->
            <div class="client-hero-card">
                <div class="client-name-title"><?php echo htmlspecialchars($client_name, ENT_QUOTES, 'UTF-8'); ?></div>
                <div class="client-meta-row">
                    <span class="client-id-badge">ID: <?php echo htmlspecialchars($client_id, ENT_QUOTES, 'UTF-8'); ?></span>
                    <?php if ($client_id === 'C-01'): ?>
                        <span class="client-tier-badge tier-c01">Utility Tier</span>
                    <?php elseif ($client_id === 'C-02'): ?>
                        <span class="client-tier-badge tier-c02">Infra Tier</span>
                    <?php else: ?>
                        <span class="client-tier-badge tier-c03">Enterprise All Access</span>
                    <?php endif; ?>
                </div>
            </div>

            <!-- Syndicated Report Catalog with Entitlement Statuses -->
            <div>
                <div class="sidebar-header">
                    <span class="sidebar-heading">Syndicated Reports Catalog</span>
                    <span style="font-size: 11px; color: var(--text-dim);"><?php echo count($reports_catalog ?? []); ?> reports</span>
                </div>
                
                <div class="catalog-list">
                    <?php if (!empty($reports_catalog)): ?>
                        <?php foreach ($reports_catalog as $rep): ?>
                            <?php 
                                $card_class = 'report-card-locked';
                                if ($client_id === 'C-03') {
                                    $card_class = 'report-card-enterprise';
                                } elseif ($rep['is_entitled']) {
                                    $card_class = $rep['is_public'] ? 'report-card-public' : 'report-card-purchased';
                                }
                            ?>
                            <div class="report-card <?php echo $card_class; ?>">
                                <div class="report-card-top">
                                    <span class="report-code"><?php echo htmlspecialchars($rep['report_id'], ENT_QUOTES, 'UTF-8'); ?></span>
                                    <span class="report-status-badge <?php echo $rep['status_class']; ?>">
                                        <?php echo $rep['icon']; ?> <?php echo htmlspecialchars($rep['status_label'], ENT_QUOTES, 'UTF-8'); ?>
                                    </span>
                                </div>
                                <div class="report-title-text"><?php echo htmlspecialchars($rep['title'], ENT_QUOTES, 'UTF-8'); ?></div>
                                <div class="report-card-footer">
                                    <span class="report-sector-tag"><?php echo htmlspecialchars($rep['sector'], ENT_QUOTES, 'UTF-8'); ?></span>
                                    <?php if (!$rep['is_entitled'] && $client_id !== 'C-03'): ?>
                                        <button type="button" class="btn-upgrade-action" onclick="openUpgradeModal('<?php echo htmlspecialchars($rep['report_id'], ENT_QUOTES, 'UTF-8'); ?>', '<?php echo htmlspecialchars(addslashes($rep['title']), ENT_QUOTES, 'UTF-8'); ?>', '<?php echo htmlspecialchars($rep['sector'], ENT_QUOTES, 'UTF-8'); ?>')">
                                            Upgrade
                                        </button>
                                    <?php else: ?>
                                        <span><?php echo htmlspecialchars($rep['year'] ?? '2025', ENT_QUOTES, 'UTF-8'); ?></span>
                                    <?php endif; ?>
                                </div>
                            </div>
                        <?php endforeach; ?>
                    <?php endif; ?>
                </div>
            </div>

            <!-- C-03 Enterprise Advisory & Upgrade Panel -->
            <?php if ($client_id === 'C-03'): ?>
                <div class="c03-advisory-panel">
                    <div class="advisory-badge-row">
                        <span class="advisory-tag">Bespoke Advisory Upgrades</span>
                    </div>
                    <div class="advisory-actions-grid">
                        <button type="button" class="btn-advisory-action" onclick="sendPromptPreset('What will the global smart water meter market size be in the year 2045 based on your reports?')">
                            2045 Long-Range Projection &rarr;
                        </button>
                        <button type="button" class="btn-advisory-action" onclick="sendPromptPreset('What is the expected market share of sodium-ion commercial heat pumps in 2030 according to R-104?')">
                            Sodium-Ion Heat Pump Metric &rarr;
                        </button>
                        <button type="button" class="btn-advisory-action" onclick="sendPromptPreset('Calculate the Compound Annual Growth Rate (CAGR) for North America smart grid sensors between 2024 (USD 2.15B) and 2030 (USD 4.32B) from report R-105.')">
                            Smart Grid Sensors CAGR &rarr;
                        </button>
                    </div>
                </div>
            <?php endif; ?>

            <!-- Escalations Section (Clean Scrollable Container) -->
            <div class="escalations-wrapper">
                <div class="sidebar-header">
                    <span class="sidebar-heading">Escalation Tickets</span>
                    <span style="font-size: 11px; color: var(--text-dim);"><?php echo count($escalations ?? []); ?></span>
                </div>
                <div class="escalations-scroll">
                    <?php if (!empty($escalations)): ?>
                        <?php foreach ($escalations as $esc): ?>
                            <div class="escalation-item">
                                <div style="display: flex; justify-content: space-between;">
                                    <strong style="color: #f87171; font-family: monospace;"><?php echo htmlspecialchars($esc['ticket_id'], ENT_QUOTES, 'UTF-8'); ?></strong>
                                    <span style="color: #fca5a5; font-size: 10px; text-transform: uppercase; font-weight: 700;"><?php echo htmlspecialchars($esc['status'], ENT_QUOTES, 'UTF-8'); ?></span>
                                </div>
                                <div style="color: #cbd5e1; font-size: 11px; margin-top: 2px;"><?php echo htmlspecialchars($esc['reason'], ENT_QUOTES, 'UTF-8'); ?></div>
                            </div>
                        <?php endforeach; ?>
                    <?php else: ?>
                        <div style="font-size: 11px; color: var(--text-dim); padding: 4px 0;">No active escalation tickets.</div>
                    <?php endif; ?>
                </div>
            </div>
        </aside>

        <!-- Main Chat Section -->
        <main class="chat-main">
            <!-- Status Header -->
            <div class="chat-status-bar">
                <div class="status-indicator-group">
                    <span class="status-indicator-item">
                        <span class="indicator-dot dot-green"></span> RAG Entitlements Active
                    </span>
                    <span class="status-indicator-item">
                        <span class="indicator-dot dot-blue"></span> ChromaDB Connected
                    </span>
                </div>
                <div>Session: <span style="font-family: monospace; color: #94a3b8;"><?php echo htmlspecialchars($client_id, ENT_QUOTES, 'UTF-8'); ?></span></div>
            </div>

            <!-- Messages Viewport -->
            <div class="messages-viewport" id="messagesViewport">
                <!-- Initial Welcome Banner -->
                <div class="msg-row msg-assistant">
                    <div class="msg-bubble">
                        <div class="copilot-author-badge">Project Atlas Copilot</div>
                        <div class="formatted-content">
                            Hello! I am your AI Market Research Copilot for <strong><?php echo htmlspecialchars($client_name, ENT_QUOTES, 'UTF-8'); ?></strong>.
                            <br><br>
                            You have access to your purchased syndicated market reports. Queries are verified against source citations, financial calculations follow deterministic formulas, and conflicting reports are reconciled side-by-side without averaging.
                        </div>
                    </div>
                </div>

                <!-- Initial History Rendering -->
                <?php if (!empty($history)): ?>
                    <?php foreach ($history as $h): ?>
                        <div class="msg-row msg-<?php echo ($h['role'] === 'user') ? 'user' : 'assistant'; ?>">
                            <div class="msg-bubble">
                                <?php if ($h['role'] === 'assistant'): ?>
                                    <div class="copilot-author-badge">Project Atlas Copilot</div>
                                <?php endif; ?>
                                <div class="formatted-content"><?php echo htmlspecialchars($h['content'], ENT_QUOTES, 'UTF-8'); ?></div>
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

            <!-- Quick-Action Suggestions Bar -->
            <div class="quick-prompts-bar">
                <button type="button" class="prompt-chip" onclick="sendPromptPreset('What was the global smart water meter market size in 2024?')">
                    2024 Smart Water Market (R-101)
                </button>
                <button type="button" class="prompt-chip" onclick="sendPromptPreset('Compare the 2024 global smart water meter market estimates in report R-101 and report R-102. Explain the difference in market size and cite the report pages.')">
                    Compare R-101 vs R-102
                </button>
                <button type="button" class="prompt-chip" onclick="sendPromptPreset('Using report R-101, what is the projected 2030 market size for the APAC smart water meter market? Show your calculation and assumptions.')">
                    Calculate APAC 2030 Size
                </button>
                <button type="button" class="prompt-chip" onclick="sendPromptPreset('Which sector has the highest number of published market research reports in the catalog?')">
                    Catalog Sector Distribution
                </button>
            </div>

            <!-- Error Banner -->
            <div id="alertBanner" class="alert-banner" style="display: none;">
                <span id="alertText">An error occurred while connecting to the Report Copilot.</span>
                <button type="button" id="retryBtn" class="btn-retry">Retry Question</button>
            </div>

            <!-- Loading Indicator -->
            <div id="loadingIndicator" style="display: none;">
                <span>Consulting entitled reports &amp; verifying citations...</span>
            </div>

            <!-- Chat Input Bar -->
            <div class="chat-input-bar">
                <input type="hidden" name="<?php echo htmlspecialchars($csrf_token, ENT_QUOTES, 'UTF-8'); ?>" id="csrf_token" value="<?php echo htmlspecialchars($csrf_hash, ENT_QUOTES, 'UTF-8'); ?>">

                <div class="input-container">
                    <textarea id="chatInput" class="chat-textarea" placeholder="Ask a question about your market reports..." rows="1" maxlength="2000"></textarea>
                    <button type="button" id="sendBtn" class="btn-send">Send</button>
                </div>
            </div>
        </main>
    </div>

    <!-- Upgrade Request Modal (Always Hidden by Default, Rendered Fixed in Center) -->
    <div class="modal-overlay" id="upgradeModal" style="display: none;">
        <div class="modal-content">
            <div class="modal-header">
                <h3 class="modal-title">Report Licensing &amp; Upgrade</h3>
                <button type="button" class="btn-close-modal" onclick="closeUpgradeModal()">&times;</button>
            </div>
            <div class="modal-body">
                <p>Selected Report: <strong id="modalReportCode" style="color: #60a5fa; font-family: monospace;">R-101</strong></p>
                
                <div class="modal-meta-box">
                    <div><strong>Title:</strong> <span id="modalReportTitle">Global Smart Water Meter Market 2025</span></div>
                    <div><strong>Sector:</strong> <span id="modalReportSector">Utilities</span></div>
                    <div><strong>Status:</strong> <span id="modalReportStatus" style="color: #fbbf24; font-weight: 600;">License Required</span></div>
                </div>

                <p style="color: var(--text-muted); font-size: 12px;">
                    This report contains comprehensive regional projections, competitive vendor market shares, and proprietary MDM software datasets.
                </p>
            </div>
            <div class="modal-actions">
                <button type="button" class="btn-modal-cancel" onclick="closeUpgradeModal()">Cancel</button>
                <button type="button" class="btn-modal-confirm" id="modalAskBtn" onclick="askCopilotUpgrade()">
                    Ask Copilot for Scope &amp; Upgrade
                </button>
            </div>
        </div>
    </div>

    <!-- Frontend Script -->
    <script src="<?php echo base_url('assets/js/portal.js'); ?>"></script>
</body>
</html>
