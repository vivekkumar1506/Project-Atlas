<?php
defined('BASEPATH') OR exit('No direct script access allowed');

class Chat extends CI_Controller {

    public function __construct() {
        parent::__construct();
        $this->load->library('session');
        $this->load->library('Atlas_api');
        $this->load->model('Chat_model');
        $this->load->helper('url');
        $this->load->helper('security');

        // Initialize default authenticated session if empty
        if (!$this->session->userdata('logged_in')) {
            $this->session->set_userdata(array(
                'client_id'   => 'C-01',
                'client_name' => 'Northwind Utilities (Purchased: R-101, R-103)',
                'logged_in'   => TRUE
            ));
        }
    }

    /**
     * Render main chat view with CSRF tokens and client context.
     */
    public function index() {
        $client_id   = $this->session->userdata('client_id');
        $client_name = $this->session->userdata('client_name');

        // Fetch initial history
        $history = $this->Chat_model->get_client_history($client_id, 25);

        // Fetch escalations
        $escalations = $this->Chat_model->get_client_escalations($client_id, 10);

        $data = array(
            'client_id'     => $client_id,
            'client_name'   => $client_name,
            'history'       => $history,
            'escalations'   => $escalations,
            'csrf_token'    => $this->security->get_csrf_token_name(),
            'csrf_hash'     => $this->security->get_csrf_hash()
        );

        $this->load->view('chat_view', $data);
    }

    /**
     * AJAX endpoint to submit question to FastAPI AI backend.
     */
    public function ask() {
        // Enforce JSON output header
        $this->output->set_content_type('application/json');

        // Verify authenticated session
        $client_id = $this->session->userdata('client_id');
        if (empty($client_id)) {
            $this->output->set_status_header(401);
            echo json_encode(array(
                'status'  => 'error',
                'message' => 'Unauthorized session. Please login.'
            ));
            return;
        }

        // Get and sanitize question input
        $question = trim($this->input->post('question', TRUE));

        // 1. Validate empty questions
        if (empty($question)) {
            $this->output->set_status_header(400);
            echo json_encode(array(
                'status'  => 'error',
                'message' => 'Question cannot be empty. Please enter your market research question.'
            ));
            return;
        }

        // 2. Validate maximum length (PRD limit: 2000 chars)
        $maxLength = (int)$this->config->item('atlas_max_question_length') ?: 2000;
        if (mb_strlen($question) > $maxLength) {
            $this->output->set_status_header(400);
            echo json_encode(array(
                'status'  => 'error',
                'message' => "Question exceeds maximum allowed length of {$maxLength} characters."
            ));
            return;
        }

        // Create or get conversation session
        $conversation_id = $this->input->post('conversation_id');
        if (empty($conversation_id)) {
            $conversation_id = 'conv_' . substr(md5(uniqid(mt_rand(), true)), 0, 12);
        }
        $this->Chat_model->get_or_create_conversation($conversation_id, $client_id, $question);

        // Save user message turn
        $user_msg_id = 'msg_' . substr(md5(uniqid(mt_rand(), true)), 0, 12);
        $this->Chat_model->save_message($user_msg_id, $conversation_id, $client_id, 'user', $question);

        // Server-side call to FastAPI backend using server API Key
        $result = $this->atlas_api->ask($client_id, $question, $conversation_id);

        // Handle FastAPI failure or timeout (AT-08: Graceful fallback)
        if (!$result['success']) {
            $this->output->set_status_header(503);
            echo json_encode(array(
                'status'          => 'error',
                'message'         => $result['error'],
                'code'            => isset($result['code']) ? $result['code'] : 'SERVICE_UNAVAILABLE',
                'conversation_id' => $conversation_id,
                'csrf_hash'       => $this->security->get_csrf_hash()
            ));
            return;
        }

        $apiData = $result['data'];
        $assistant_msg_id = 'msg_' . substr(md5(uniqid(mt_rand(), true)), 0, 12);

        // Save assistant message to MySQL
        $this->Chat_model->save_message(
            $assistant_msg_id,
            $conversation_id,
            $client_id,
            'assistant',
            $apiData['answer'],
            isset($apiData['confidence']) ? $apiData['confidence'] : NULL,
            !empty($apiData['escalated']),
            $apiData
        );

        echo json_encode(array(
            'status'          => 'success',
            'conversation_id' => $conversation_id,
            'message_id'      => $assistant_msg_id,
            'answer'          => $apiData['answer'],
            'citations'       => isset($apiData['citations']) ? $apiData['citations'] : array(),
            'confidence'      => isset($apiData['confidence']) ? $apiData['confidence'] : 0.0,
            'conflicts'       => isset($apiData['conflicts']) ? $apiData['conflicts'] : array(),
            'derived_values'  => isset($apiData['derived_values']) ? $apiData['derived_values'] : array(),
            'escalated'       => !empty($apiData['escalated']),
            'escalation_reason' => isset($apiData['escalation_reason']) ? $apiData['escalation_reason'] : NULL,
            'csrf_hash'       => $this->security->get_csrf_hash()
        ));
    }

    /**
     * AJAX endpoint to submit thumbs-up / thumbs-down feedback.
     */
    public function feedback() {
        $this->output->set_content_type('application/json');

        $client_id  = $this->session->userdata('client_id');
        $message_id = trim($this->input->post('message_id', TRUE));
        $rating     = trim($this->input->post('rating', TRUE)); // 'up' or 'down'
        $comment    = trim($this->input->post('comment', TRUE));

        if (!in_array($rating, array('up', 'down'))) {
            $this->output->set_status_header(400);
            echo json_encode(array('status' => 'error', 'message' => 'Rating must be either "up" or "down".'));
            return;
        }

        if (empty($message_id)) {
            $this->output->set_status_header(400);
            echo json_encode(array('status' => 'error', 'message' => 'Message ID is required.'));
            return;
        }

        $res = $this->Chat_model->record_feedback($message_id, $client_id, $rating, $comment);

        if (!$res['success']) {
            $this->output->set_status_header(403);
            echo json_encode(array('status' => 'error', 'message' => $res['error']));
            return;
        }

        echo json_encode(array(
            'status'    => 'success',
            'action'    => $res['action'],
            'message'   => 'Thank you for your feedback.',
            'csrf_hash' => $this->security->get_csrf_hash()
        ));
    }

    /**
     * AJAX endpoint to load conversation history for current client.
     */
    public function history() {
        $this->output->set_content_type('application/json');
        $client_id = $this->session->userdata('client_id');

        $history = $this->Chat_model->get_client_history($client_id, 50);

        echo json_encode(array(
            'status'    => 'success',
            'client_id' => $client_id,
            'history'   => $history
        ));
    }

    /**
     * AJAX endpoint to fetch escalations for current client.
     */
    public function escalations() {
        $this->output->set_content_type('application/json');
        $client_id = $this->session->userdata('client_id');

        $escalations = $this->Chat_model->get_client_escalations($client_id, 20);

        echo json_encode(array(
            'status'      => 'success',
            'client_id'   => $client_id,
            'escalations' => $escalations
        ));
    }
}
