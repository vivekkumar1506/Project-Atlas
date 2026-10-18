<?php
defined('BASEPATH') OR exit('No direct script access allowed');

/*
|--------------------------------------------------------------------------
| Project Atlas - FastAPI AI Integration Settings
|--------------------------------------------------------------------------
*/

$config['atlas_api_base_url'] = getenv('FASTAPI_BASE_URL') ?: 'http://127.0.0.1:8000';
$config['atlas_api_key']      = getenv('API_KEY') ?: 'atlas_dev_secret_key_2026';

// Request timeout thresholds (Under 30s as per PRD non-functional requirements)
$config['atlas_connect_timeout'] = 5;  // seconds
$config['atlas_read_timeout']    = 28; // seconds

// Input boundaries
$config['atlas_max_question_length'] = 2000;
$config['atlas_min_question_length'] = 2;
