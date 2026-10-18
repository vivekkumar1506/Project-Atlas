<?php
/**
 * Project Atlas - CodeIgniter 3 Core Engine Runtime
 * Implements the standard CI3 request lifecycle:
 * URI routing -> Controller dispatch -> CSRF verification -> Model/Library loading -> Output rendering.
 */

if (!defined('BASEPATH')) exit('No direct script access allowed');

define('CI_VERSION', '3.1.13');

// Global CI super-object instance container
class CI_Base {
    private static $instance;

    public function __construct() {
        self::$instance =& $this;
    }

    public static function &get_instance() {
        return self::$instance;
    }
}

function &get_instance() {
    return CI_Base::get_instance();
}

function base_url($uri = '') {
    $CI =& get_instance();
    $base = $CI->config->item('base_url');
    return rtrim($base, '/') . '/' . ltrim($uri, '/');
}

function redirect($uri = '') {
    header('Location: ' . base_url($uri));
    exit;
}

function log_message($level, $message) {
    error_log("[CI3-{$level}] " . $message);
}

// -----------------------------------------------------------------------------
// Core Component: Config Loader
// -----------------------------------------------------------------------------
class CI_Config {
    public $config = array();

    public function __construct() {
        if (file_exists(APPPATH . 'config/config.php')) {
            require(APPPATH . 'config/config.php');
            $this->config = $config;
        }
    }

    public function item($item) {
        return isset($this->config[$item]) ? $this->config[$item] : NULL;
    }

    public function load($file) {
        $path = APPPATH . 'config/' . $file . '.php';
        if (file_exists($path)) {
            require($path);
            if (isset($config)) {
                $this->config = array_merge($this->config, $config);
            }
        }
    }
}

// -----------------------------------------------------------------------------
// Core Component: Input & CSRF Security
// -----------------------------------------------------------------------------
class CI_Input {
    public function post($index = NULL, $xss_clean = FALSE) {
        if ($index === NULL) return $_POST;
        if (!isset($_POST[$index])) return NULL;
        $val = $_POST[$index];
        if ($xss_clean && is_string($val)) {
            $val = htmlspecialchars($val, ENT_QUOTES, 'UTF-8');
        }
        return $val;
    }

    public function get($index = NULL) {
        if ($index === NULL) return $_GET;
        return isset($_GET[$index]) ? $_GET[$index] : NULL;
    }
}

class CI_Security {
    protected $csrf_token_name = 'atlas_csrf_token';
    protected $csrf_hash;

    public function __construct() {
        if (session_status() === PHP_SESSION_NONE) {
            @session_start();
        }
        if (!isset($_SESSION['atlas_csrf_hash'])) {
            $_SESSION['atlas_csrf_hash'] = bin2hex(random_bytes(16));
        }
        $this->csrf_hash = $_SESSION['atlas_csrf_hash'];
    }

    public function get_csrf_token_name() {
        return $this->csrf_token_name;
    }

    public function get_csrf_hash() {
        return $this->csrf_hash;
    }

    public function csrf_verify() {
        if (strtoupper($_SERVER['REQUEST_METHOD']) === 'POST') {
            $token = isset($_POST[$this->csrf_token_name]) ? $_POST[$this->csrf_token_name] : '';
            if (empty($token) && isset($_SERVER['HTTP_X_CSRF_TOKEN'])) {
                $token = $_SERVER['HTTP_X_CSRF_TOKEN'];
            }
            if (!hash_equals($this->csrf_hash, $token)) {
                header('HTTP/1.1 403 Forbidden');
                header('Content-Type: application/json');
                echo json_encode(array(
                    'status' => 'error',
                    'message' => 'The action you have requested is not allowed. CSRF token validation failed.'
                ));
                exit;
            }
        }
    }
}

// -----------------------------------------------------------------------------
// Core Component: Output Buffer
// -----------------------------------------------------------------------------
class CI_Output {
    protected $headers = array();
    protected $final_output = '';

    public function set_content_type($mime_type) {
        header('Content-Type: ' . $mime_type);
        return $this;
    }

    public function set_status_header($code = 200) {
        http_response_code($code);
        return $this;
    }
}

// -----------------------------------------------------------------------------
// Core Component: Session Management
// -----------------------------------------------------------------------------
class CI_Session {
    public function __construct() {
        if (session_status() === PHP_SESSION_NONE) {
            @session_start();
        }
    }

    public function userdata($item = NULL) {
        if ($item === NULL) return $_SESSION;
        return isset($_SESSION[$item]) ? $_SESSION[$item] : NULL;
    }

    public function set_userdata($data, $value = NULL) {
        if (is_array($data)) {
            foreach ($data as $k => $v) {
                $_SESSION[$k] = $v;
            }
        } else {
            $_SESSION[$data] = $value;
        }
    }

    public function sess_destroy() {
        $_SESSION = array();
        if (session_status() === PHP_SESSION_ACTIVE) {
            @session_destroy();
        }
    }
}

// -----------------------------------------------------------------------------
// Core Component: Database Layer (PDO / MySQLi wrapper)
// -----------------------------------------------------------------------------
class CI_DB_Result {
    protected $rows;

    public function __construct($rows) {
        $this->rows = $rows ?: array();
    }

    public function num_rows() {
        return count($this->rows);
    }

    public function result_array() {
        return $this->rows;
    }

    public function row() {
        return !empty($this->rows) ? (object)$this->rows[0] : NULL;
    }
}

class CI_DB {
    protected $pdo;

    public function __construct() {
        require(APPPATH . 'config/database.php');
        $conf = $db['default'];
        $dsn = "mysql:host={$conf['hostname']};port={$conf['port']};dbname={$conf['database']};charset=utf8mb4";
        try {
            $this->pdo = new PDO($dsn, $conf['username'], $conf['password'], array(
                PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
                PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC
            ));
        } catch (Exception $e) {
            log_message('error', 'MySQL connection failure: ' . $e->getMessage());
        }
    }

    public function get_where($table, $where = array(), $limit = NULL) {
        $sql = "SELECT * FROM `{$table}`";
        $params = array();
        if (!empty($where)) {
            $clauses = array();
            foreach ($where as $k => $v) {
                $clauses[] = "`{$k}` = :{$k}";
                $params[":{$k}"] = $v;
            }
            $sql .= " WHERE " . implode(" AND ", $clauses);
        }
        if ($limit) {
            $sql .= " LIMIT " . (int)$limit;
        }
        $stmt = $this->pdo->prepare($sql);
        $stmt->execute($params);
        return new CI_DB_Result($stmt->fetchAll());
    }

    public function insert($table, $data) {
        $keys = array_keys($data);
        $fields = '`' . implode('`, `', $keys) . '`';
        $placeholders = ':' . implode(', :', $keys);
        $sql = "INSERT INTO `{$table}` ({$fields}) VALUES ({$placeholders})";
        $stmt = $this->pdo->prepare($sql);
        $params = array();
        foreach ($data as $k => $v) {
            $params[":{$k}"] = $v;
        }
        return $stmt->execute($params);
    }

    // Query Builder chaining support
    protected $builder_select = '*';
    protected $builder_from = '';
    protected $builder_joins = array();
    protected $builder_wheres = array();
    protected $builder_params = array();
    protected $builder_order = '';
    protected $builder_limit = '';

    public function select($select) {
        $this->builder_select = $select;
        return $this;
    }

    public function from($from) {
        $this->builder_from = $from;
        return $this;
    }

    public function join($table, $cond) {
        $this->builder_joins[] = "JOIN {$table} ON {$cond}";
        return $this;
    }

    public function where($field, $val) {
        $paramName = ':p_' . count($this->builder_params);
        $this->builder_wheres[] = "{$field} = {$paramName}";
        $this->builder_params[$paramName] = $val;
        return $this;
    }

    public function order_by($col, $dir = 'ASC') {
        $this->builder_order = "ORDER BY {$col} {$dir}";
        return $this;
    }

    public function limit($limit) {
        $this->builder_limit = "LIMIT " . (int)$limit;
        return $this;
    }

    public function get() {
        $sql = "SELECT {$this->builder_select} FROM {$this->builder_from}";
        if (!empty($this->builder_joins)) {
            $sql .= ' ' . implode(' ', $this->builder_joins);
        }
        if (!empty($this->builder_wheres)) {
            $sql .= ' WHERE ' . implode(' AND ', $this->builder_wheres);
        }
        if (!empty($this->builder_order)) {
            $sql .= ' ' . $this->builder_order;
        }
        if (!empty($this->builder_limit)) {
            $sql .= ' ' . $this->builder_limit;
        }

        $stmt = $this->pdo->prepare($sql);
        $stmt->execute($this->builder_params);

        // Reset builder state
        $this->builder_select = '*';
        $this->builder_from = '';
        $this->builder_joins = array();
        $this->builder_wheres = array();
        $this->builder_params = array();
        $this->builder_order = '';
        $this->builder_limit = '';

        return new CI_DB_Result($stmt->fetchAll());
    }

    public function update($table, $data) {
        $sets = array();
        $params = array();
        foreach ($data as $k => $v) {
            $sets[] = "`{$k}` = :set_{$k}";
            $params[":set_{$k}"] = $v;
        }
        $sql = "UPDATE `{$table}` SET " . implode(', ', $sets);
        if (!empty($this->builder_wheres)) {
            $sql .= ' WHERE ' . implode(' AND ', $this->builder_wheres);
            $params = array_merge($params, $this->builder_params);
        }
        $stmt = $this->pdo->prepare($sql);
        $res = $stmt->execute($params);

        $this->builder_wheres = array();
        $this->builder_params = array();
        return $res;
    }
}

// -----------------------------------------------------------------------------
// Core Component: Loader
// -----------------------------------------------------------------------------
class CI_Loader {
    public function library($library) {
        $CI =& get_instance();
        $libName = basename($library);
        $propName = strtolower($libName);
        if ($propName === 'session') {
            $CI->session = new CI_Session();
            return;
        }
        $path = APPPATH . 'libraries/' . $libName . '.php';
        if (file_exists($path)) {
            require_once($path);
            $CI->$propName = new $libName();
        }
    }

    public function model($model) {
        $CI =& get_instance();
        $modelName = basename($model);
        $propName = $modelName;
        $path = APPPATH . 'models/' . $modelName . '.php';
        if (file_exists($path)) {
            require_once($path);
            $CI->$propName = new $modelName();
        }
    }

    public function view($view, $vars = array(), $return = FALSE) {
        extract($vars);
        $path = APPPATH . 'views/' . $view . '.php';
        if ($return) {
            ob_start();
            require($path);
            return ob_get_clean();
        }
        require($path);
    }

    public function helper($helper) {
        // Helpers like url or security
    }

    public function database() {
        $CI =& get_instance();
        if (!isset($CI->db)) {
            $CI->db = new CI_DB();
        }
    }

    public function config($item) {
        $CI =& get_instance();
        $CI->config->load($item);
    }
}

// -----------------------------------------------------------------------------
// Base Controller & Model
// -----------------------------------------------------------------------------
class CI_Controller extends CI_Base {
    public $load;
    public $config;
    public $input;
    public $output;
    public $security;
    public $session;
    public $db;

    public function __construct() {
        parent::__construct();
        $this->config   = new CI_Config();
        $this->load     = new CI_Loader();
        $this->input    = new CI_Input();
        $this->output   = new CI_Output();
        $this->security = new CI_Security();
        $this->session  = new CI_Session();

        // Enforce CSRF verification for state-changing browser requests
        if ($this->config->item('csrf_protection')) {
            $this->security->csrf_verify();
        }
    }
}

class CI_Model {
    public $db;
    public $load;

    public function __construct() {
        $CI =& get_instance();
        $this->load =& $CI->load;
        $this->db   =& $CI->db;
    }
}

// -----------------------------------------------------------------------------
// Front Controller Request Dispatcher
// -----------------------------------------------------------------------------
function ci_dispatch() {
    $uri = isset($_SERVER['PATH_INFO']) ? $_SERVER['PATH_INFO'] : (isset($_SERVER['REQUEST_URI']) ? $_SERVER['REQUEST_URI'] : '/');
    // Strip query string and script name
    $uri = strtok($uri, '?');
    $uri = preg_replace('#^/index\.php/?#i', '/', $uri);
    $segments = array_values(array_filter(explode('/', trim($uri, '/'))));

    $controller = !empty($segments[0]) ? ucfirst(strtolower($segments[0])) : 'Chat';
    $method = !empty($segments[1]) ? strtolower($segments[1]) : 'index';
    $params = array_slice($segments, 2);

    $file = APPPATH . 'controllers/' . $controller . '.php';
    if (!file_exists($file)) {
        header('HTTP/1.1 404 Not Found');
        echo "404 Not Found: Controller {$controller} does not exist.";
        exit;
    }

    require_once($file);
    if (!class_exists($controller)) {
        header('HTTP/1.1 404 Not Found');
        echo "404 Not Found: Class {$controller} not defined.";
        exit;
    }

    $instance = new $controller();
    if (!method_exists($instance, $method)) {
        header('HTTP/1.1 404 Not Found');
        echo "404 Not Found: Action {$method} not found in {$controller}.";
        exit;
    }

    call_user_func_array(array($instance, $method), $params);
}
