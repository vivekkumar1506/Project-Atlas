<?php
defined('BASEPATH') OR exit('No direct script access allowed');

/*
|--------------------------------------------------------------------------
| Project Atlas - URI Routing
|--------------------------------------------------------------------------
*/

$route['default_controller'] = 'chat';
$route['404_override'] = '';
$route['translate_uri_dashes'] = FALSE;

// Chat & AJAX routes
$route['chat'] = 'chat/index';
$route['chat/ask'] = 'chat/ask';
$route['chat/history'] = 'chat/history';
$route['chat/feedback'] = 'chat/feedback';
$route['chat/escalations'] = 'chat/escalations';

// Auth / Client selection
$route['auth/switch_client/(:any)'] = 'auth/switch_client/$1';
$route['auth/logout'] = 'auth/logout';
