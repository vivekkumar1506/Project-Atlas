<?php
/**
 * CodeIgniter 3 Front Controller
 *
 * Project Atlas — AI Market Research Report Copilot
 */

define('ENVIRONMENT', isset($_SERVER['CI_ENV']) ? $_SERVER['CI_ENV'] : 'development');

switch (ENVIRONMENT) {
    case 'development':
        error_reporting(-1);
        ini_set('display_errors', 1);
        break;
    case 'testing':
    case 'production':
        ini_set('display_errors', 0);
        error_reporting(E_ALL & ~E_NOTICE & ~E_DEPRECATED & ~E_STRICT & ~E_USER_NOTICE & ~E_USER_DEPRECATED);
        break;
    default:
        header('HTTP/1.1 503 Service Unavailable.', TRUE, 503);
        echo 'The application environment is not set correctly.';
        exit(1);
}

$system_path = 'system';
$application_folder = 'application';

define('SELF', pathinfo(__FILE__, PATHINFO_BASENAME));
define('BASEPATH', str_replace('\\', '/', realpath(__DIR__ . '/' . $system_path)) . '/');
define('FCPATH', dirname(__FILE__) . '/');
define('SYSDIR', basename(BASEPATH));
define('APPPATH', realpath(__DIR__ . '/' . $application_folder) . '/');

require_once BASEPATH . 'core/CodeIgniter.php';

// Dispatch incoming request
ci_dispatch();
