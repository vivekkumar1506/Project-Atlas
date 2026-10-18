<?php
/**
 * Project Atlas — PHP Built-in Server Router for CodeIgniter 3
 * Enables clean routing (/chat/send, /chat/history, /auth/switch_client)
 * while serving static CSS, JS, and font assets directly.
 */

$uri = urldecode(parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH));

// Serve static assets directly if they exist
if ($uri !== '/' && file_exists(__DIR__ . $uri)) {
    return false;
}

// Route all other requests through CodeIgniter 3 front controller
$_SERVER['SCRIPT_NAME'] = '/index.php';
require_once __DIR__ . '/index.php';
