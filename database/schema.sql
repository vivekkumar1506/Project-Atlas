-- =============================================================================
-- Project Atlas - Complete Relational Schema
-- Aligned with System Architecture & Database Relationship Diagram
-- =============================================================================

CREATE DATABASE IF NOT EXISTS `project_atlas`
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_unicode_ci;

USE `project_atlas`;

-- Disable foreign key checks during schema creation/refresh
SET FOREIGN_KEY_CHECKS = 0;

-- -----------------------------------------------------------------------------
-- 1. Clients & Access Control (Top Layer)
-- -----------------------------------------------------------------------------

-- Client accounts and status
CREATE TABLE IF NOT EXISTS `clients` (
    `client_id` VARCHAR(50) NOT NULL PRIMARY KEY,
    `name` VARCHAR(255) NOT NULL,
    `status` ENUM('active', 'suspended', 'inactive') NOT NULL DEFAULT 'active',
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX `idx_clients_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Reports metadata, access policies, and ingestion status
CREATE TABLE IF NOT EXISTS `reports` (
    `report_id` VARCHAR(50) NOT NULL PRIMARY KEY,
    `title` VARCHAR(255) NOT NULL,
    `sector` VARCHAR(100) NOT NULL,
    `region` VARCHAR(100) NOT NULL,
    `year` INT NOT NULL,
    `source_type` VARCHAR(50) NOT NULL DEFAULT 'PDF',
    `access_policy` VARCHAR(50) NOT NULL DEFAULT 'restricted',
    `ingestion_status` ENUM('pending', 'ingested', 'failed') NOT NULL DEFAULT 'pending',
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX `idx_reports_sector_region` (`sector`, `region`, `year`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Which reports each client can access (One client has many entitlements)
CREATE TABLE IF NOT EXISTS `client_report_entitlements` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `client_id` VARCHAR(50) NOT NULL,
    `report_id` VARCHAR(50) NOT NULL,
    `access_scope` VARCHAR(50) NOT NULL DEFAULT 'full',
    `valid_from` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `valid_to` DATETIME NULL,
    `status` ENUM('active', 'revoked', 'expired') NOT NULL DEFAULT 'active',
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_entitlements_client` FOREIGN KEY (`client_id`) REFERENCES `clients` (`client_id`) ON DELETE CASCADE,
    CONSTRAINT `fk_entitlements_report` FOREIGN KEY (`report_id`) REFERENCES `reports` (`report_id`) ON DELETE CASCADE,
    UNIQUE KEY `uk_client_report` (`client_id`, `report_id`),
    INDEX `idx_entitlements_client_status` (`client_id`, `status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Structured Market Metrics for Aggregate Read-only SQL queries
CREATE TABLE IF NOT EXISTS `market_metrics` (
    `metric_id` INT AUTO_INCREMENT PRIMARY KEY,
    `report_id` VARCHAR(50) NOT NULL,
    `metric_name` VARCHAR(100) NOT NULL,
    `value` DECIMAL(15, 4) NOT NULL,
    `unit` VARCHAR(50) NOT NULL,
    `geography` VARCHAR(100) NOT NULL,
    `segment` VARCHAR(100) NOT NULL,
    `period` VARCHAR(50) NOT NULL,
    `source_location` VARCHAR(100) NULL,
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_metrics_report` FOREIGN KEY (`report_id`) REFERENCES `reports` (`report_id`) ON DELETE CASCADE,
    INDEX `idx_metrics_lookup` (`metric_name`, `geography`, `period`),
    INDEX `idx_metrics_report` (`report_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------------------------------
-- 2. Conversations & Messages (Middle Layer: conversations -> messages)
-- -----------------------------------------------------------------------------

-- Conversations session header
CREATE TABLE IF NOT EXISTS `conversations` (
    `conversation_id` VARCHAR(64) NOT NULL PRIMARY KEY,
    `client_id` VARCHAR(50) NOT NULL,
    `user_reference` VARCHAR(100) NULL,
    `title` VARCHAR(255) NULL,
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT `fk_conversations_client` FOREIGN KEY (`client_id`) REFERENCES `clients` (`client_id`) ON DELETE CASCADE,
    INDEX `idx_conversations_client` (`client_id`, `created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Individual messages in a conversation (User queries & Assistant answers)
CREATE TABLE IF NOT EXISTS `messages` (
    `message_id` VARCHAR(64) NOT NULL PRIMARY KEY,
    `conversation_id` VARCHAR(64) NOT NULL,
    `role` ENUM('user', 'assistant', 'system') NOT NULL,
    `content` TEXT NOT NULL,
    `confidence` DECIMAL(4, 3) NULL DEFAULT NULL,
    `escalated` TINYINT(1) NOT NULL DEFAULT 0,
    `raw_payload` JSON NULL,
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_messages_conversation` FOREIGN KEY (`conversation_id`) REFERENCES `conversations` (`conversation_id`) ON DELETE CASCADE,
    INDEX `idx_messages_conversation` (`conversation_id`, `created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------------------------------
-- 3. Evidence, Feedback & Escalations (Connected to Messages/Answers)
-- -----------------------------------------------------------------------------

-- Citations: Evidence per answer
CREATE TABLE IF NOT EXISTS `citations` (
    `citation_id` INT AUTO_INCREMENT PRIMARY KEY,
    `message_id` VARCHAR(64) NOT NULL,
    `report_id` VARCHAR(50) NOT NULL,
    `source_location` VARCHAR(150) NULL,
    `page_number` INT NULL,
    `excerpt` TEXT NULL,
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_citations_message` FOREIGN KEY (`message_id`) REFERENCES `messages` (`message_id`) ON DELETE CASCADE,
    CONSTRAINT `fk_citations_report` FOREIGN KEY (`report_id`) REFERENCES `reports` (`report_id`) ON DELETE CASCADE,
    INDEX `idx_citations_message` (`message_id`),
    INDEX `idx_citations_report` (`report_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Feedback: Thumbs up / down per answer
CREATE TABLE IF NOT EXISTS `feedback` (
    `feedback_id` INT AUTO_INCREMENT PRIMARY KEY,
    `message_id` VARCHAR(64) NOT NULL,
    `conversation_id` VARCHAR(64) NULL,
    `rating` ENUM('up', 'down') NOT NULL,
    `comment` TEXT NULL,
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_feedback_message` FOREIGN KEY (`message_id`) REFERENCES `messages` (`message_id`) ON DELETE CASCADE,
    CONSTRAINT `fk_feedback_conversation` FOREIGN KEY (`conversation_id`) REFERENCES `conversations` (`conversation_id`) ON DELETE CASCADE,
    INDEX `idx_feedback_message` (`message_id`),
    INDEX `idx_feedback_conversation` (`conversation_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Escalations: Analyst follow-up for low-confidence or unresolved questions
CREATE TABLE IF NOT EXISTS `escalations` (
    `ticket_id` VARCHAR(64) NOT NULL PRIMARY KEY,
    `conversation_id` VARCHAR(64) NULL,
    `message_id` VARCHAR(64) NULL,
    `client_id` VARCHAR(50) NOT NULL,
    `question` TEXT NOT NULL,
    `reason` VARCHAR(255) NOT NULL,
    `confidence` DECIMAL(4, 3) NOT NULL DEFAULT 0.000,
    `status` ENUM('open', 'in_progress', 'resolved', 'closed') NOT NULL DEFAULT 'open',
    `assigned_to` VARCHAR(100) NULL,
    `supporting_references` JSON NULL,
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `resolved_at` TIMESTAMP NULL,
    CONSTRAINT `fk_escalations_client` FOREIGN KEY (`client_id`) REFERENCES `clients` (`client_id`) ON DELETE CASCADE,
    CONSTRAINT `fk_escalations_conversation` FOREIGN KEY (`conversation_id`) REFERENCES `conversations` (`conversation_id`) ON DELETE SET NULL,
    CONSTRAINT `fk_escalations_message` FOREIGN KEY (`message_id`) REFERENCES `messages` (`message_id`) ON DELETE SET NULL,
    INDEX `idx_escalations_status` (`status`, `created_at`),
    INDEX `idx_escalations_client` (`client_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------------------------------
-- 4. Audit, Metrics & Ingestion Monitoring (Bottom Layer)
-- -----------------------------------------------------------------------------

-- Security Events: Security audit, prompt injection attempts, unauthorized access
CREATE TABLE IF NOT EXISTS `security_events` (
    `event_id` INT AUTO_INCREMENT PRIMARY KEY,
    `event_type` VARCHAR(100) NOT NULL,
    `client_id` VARCHAR(50) NULL,
    `details_summary` TEXT NOT NULL,
    `ip_address` VARCHAR(45) NULL,
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_security_client` FOREIGN KEY (`client_id`) REFERENCES `clients` (`client_id`) ON DELETE SET NULL,
    INDEX `idx_sec_events_type` (`event_type`, `created_at`),
    INDEX `idx_sec_events_client` (`client_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Request Metrics: Latency, cost, and route tracking
CREATE TABLE IF NOT EXISTS `request_metrics` (
    `request_id` VARCHAR(64) NOT NULL PRIMARY KEY,
    `route` VARCHAR(100) NOT NULL,
    `latency_ms` INT NOT NULL,
    `token_count` INT NULL DEFAULT 0,
    `cost_estimate` DECIMAL(10, 6) NULL DEFAULT 0.000000,
    `status` VARCHAR(50) NOT NULL DEFAULT 'success',
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX `idx_metrics_route` (`route`, `created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Ingestion Runs: Ingestion pipeline execution monitoring
CREATE TABLE IF NOT EXISTS `ingestion_runs` (
    `run_id` VARCHAR(64) NOT NULL PRIMARY KEY,
    `report_id` VARCHAR(50) NOT NULL,
    `status` ENUM('pending', 'running', 'completed', 'failed') NOT NULL DEFAULT 'pending',
    `chunks_count` INT NOT NULL DEFAULT 0,
    `error_message` TEXT NULL,
    `started_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `completed_at` TIMESTAMP NULL,
    CONSTRAINT `fk_ingestion_report` FOREIGN KEY (`report_id`) REFERENCES `reports` (`report_id`) ON DELETE CASCADE,
    INDEX `idx_ingestion_report` (`report_id`),
    INDEX `idx_ingestion_status` (`status`, `started_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Re-enable foreign key checks
SET FOREIGN_KEY_CHECKS = 1;

-- =============================================================================
-- Initial Seed Baseline Data
-- =============================================================================

-- 1. Seed Clients
INSERT INTO `clients` (`client_id`, `name`, `status`)
VALUES 
    ('C-01', 'Alpha Corporate Client', 'active'),
    ('C-02', 'Beta Partner Enterprise', 'active'),
    ('C-03', 'Gamma Analytics Corp', 'active')
ON DUPLICATE KEY UPDATE `name`=VALUES(`name`);

-- 2. Seed Reports (Baseline from Appendix A)
INSERT INTO `reports` (`report_id`, `title`, `sector`, `region`, `year`, `source_type`, `access_policy`, `ingestion_status`)
VALUES
    ('R-101', 'Global Smart Water Meter Market 2025', 'Utilities', 'Global', 2025, 'PDF', 'paid', 'pending'),
    ('R-102', 'Smart Water Metering: Industry Outlook 2024', 'Utilities', 'Global', 2024, 'PDF', 'public excerpt', 'pending'),
    ('R-103', 'Residential Water Purifier Market 2025', 'Consumer Durables', 'Global', 2025, 'PDF', 'paid', 'pending'),
    ('R-104', 'European Commercial Heat Pump Market 2024', 'Energy & Utilities', 'Europe', 2024, 'PDF', 'paid', 'pending'),
    ('R-105', 'North America Smart Grid Sensors Market 2024', 'Technology', 'North America', 2024, 'PDF', 'paid', 'pending'),
    ('R-106', 'Global Industrial Wastewater Treatment Tech 2025', 'Utilities & Environmental', 'Global', 2025, 'PDF', 'paid', 'pending')
ON DUPLICATE KEY UPDATE 
    `title`=VALUES(`title`),
    `sector`=VALUES(`sector`),
    `region`=VALUES(`region`),
    `year`=VALUES(`year`),
    `access_policy`=VALUES(`access_policy`);

-- 3. Seed Client Entitlements
-- Acceptance Criteria AT-03: C-01 can access R-101 and R-103; C-02 can access R-103 only.
INSERT INTO `client_report_entitlements` (`client_id`, `report_id`, `access_scope`, `status`)
VALUES
    ('C-01', 'R-101', 'full', 'active'),
    ('C-01', 'R-103', 'full', 'active'),
    ('C-02', 'R-103', 'full', 'active'),
    ('C-03', 'R-101', 'full', 'active'),
    ('C-03', 'R-102', 'full', 'active'),
    ('C-03', 'R-103', 'full', 'active'),
    ('C-03', 'R-104', 'full', 'active'),
    ('C-03', 'R-105', 'full', 'active'),
    ('C-03', 'R-106', 'full', 'active')
ON DUPLICATE KEY UPDATE `status`=VALUES(`status`);

-- 4. Seed Market Metrics (Appendix A Table)
INSERT INTO `market_metrics` (`report_id`, `metric_name`, `value`, `unit`, `geography`, `segment`, `period`, `source_location`)
VALUES
    ('R-101', 'Market size', 4.2100, 'USD Billion', 'Global', 'Hardware, Software and Services', '2024', 'Page 8, Table 8.1'),
    ('R-101', 'CAGR', 11.2000, 'Percent', 'Global', 'Forecast window 2025-2030', '2025-2030', 'Page 8, Table 8.1'),
    ('R-101', 'Regional share', 38.0000, 'Percent', 'APAC', 'Share of global market size', '2024', 'Page 8, Table 8.1'),
    ('R-102', 'Market size', 3.8700, 'USD Billion', 'Global', 'AMR / AMI hardware only', '2024', 'Page 14'),
    ('R-102', 'CAGR', 9.8000, 'Percent', 'Global', 'Different forecast window from R-101', '2024-2029', 'Page 14'),
    ('R-102', 'Regional share', 41.0000, 'Percent', 'APAC', 'Share of hardware market', '2024', 'Page 14');
