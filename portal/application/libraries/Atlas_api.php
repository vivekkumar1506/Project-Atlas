<?php
defined('BASEPATH') OR exit('No direct script access allowed');

#[\AllowDynamicProperties]
class Atlas_api {

    protected $CI;
    protected $base_url;
    protected $api_key;
    protected $connect_timeout;
    protected $read_timeout;

    public function __construct() {
        $this->CI =& get_instance();
        $this->CI->load->config('atlas');

        $this->base_url        = rtrim($this->CI->config->item('atlas_api_base_url'), '/');
        $this->api_key         = $this->CI->config->item('atlas_api_key');
        $this->connect_timeout = (int)$this->CI->config->item('atlas_connect_timeout') ?: 5;
        $this->read_timeout    = (int)$this->CI->config->item('atlas_read_timeout') ?: 28;
    }

    /**
     * Send question to FastAPI /chat endpoint using server-side cURL.
     */
    public function ask($client_id, $question, $user_reference = NULL) {
        $endpoint = $this->base_url . '/chat';

        $payload = array(
            'client_id'      => $client_id,
            'question'       => $question,
            'user_reference' => $user_reference
        );

        $jsonData = json_encode($payload);

        $headers = array(
            'Content-Type: application/json',
            'Accept: application/json',
            'X-API-Key: ' . $this->api_key
        );

        $ch = curl_init();
        curl_setopt($ch, CURLOPT_URL, $endpoint);
        curl_setopt($ch, CURLOPT_POST, TRUE);
        curl_setopt($ch, CURLOPT_POSTFIELDS, $jsonData);
        curl_setopt($ch, CURLOPT_HTTPHEADER, $headers);
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, TRUE);
        curl_setopt($ch, CURLOPT_CONNECTTIMEOUT, $this->connect_timeout);
        curl_setopt($ch, CURLOPT_TIMEOUT, $this->read_timeout);
        curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, FALSE); // Development friendly

        $rawResponse = curl_exec($ch);
        $curlError   = curl_error($ch);
        $httpCode    = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        curl_close($ch);

        // Handle cURL network failure or timeout (PRD AT-08: API unavailable fallback)
        if ($rawResponse === FALSE || !empty($curlError)) {
            log_message('error', "FastAPI Copilot connection error: {$curlError}");
            return array(
                'success' => FALSE,
                'error'   => 'The Report Copilot is temporarily unavailable. Please retry in a moment.',
                'code'    => 'BACKEND_TIMEOUT_OR_OFFLINE'
            );
        }

        // Validate response is valid JSON
        $decoded = json_decode($rawResponse, TRUE);
        if ($decoded === NULL && json_last_error() !== JSON_ERROR_NONE) {
            log_message('error', "FastAPI invalid JSON response: " . substr($rawResponse, 0, 200));
            return array(
                'success' => FALSE,
                'error'   => 'Received an unexpected response from the AI Copilot. Please retry.',
                'code'    => 'INVALID_BACKEND_JSON'
            );
        }

        // Handle HTTP error codes
        if ($httpCode >= 400) {
            $msg = isset($decoded['detail']) ? $decoded['detail'] : 'AI Service reported an issue.';
            return array(
                'success' => FALSE,
                'error'   => $msg,
                'code'    => 'HTTP_' . $httpCode
            );
        }

        return array(
            'success' => TRUE,
            'data'    => $decoded
        );
    }

    /**
     * Check backend health check status safely.
     */
    public function check_health() {
        $endpoint = $this->base_url . '/health';
        $ch = curl_init();
        curl_setopt($ch, CURLOPT_URL, $endpoint);
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, TRUE);
        curl_setopt($ch, CURLOPT_CONNECTTIMEOUT, 3);
        curl_setopt($ch, CURLOPT_TIMEOUT, 5);
        $resp = curl_exec($ch);
        $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        curl_close($ch);

        if ($resp && $httpCode === 200) {
            return json_decode($resp, TRUE);
        }
        return array('status' => 'offline', 'connected' => FALSE);
    }
}
