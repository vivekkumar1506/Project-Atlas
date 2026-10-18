<?php
defined('BASEPATH') OR exit('No direct script access allowed');

#[\AllowDynamicProperties]
class Chat_model extends CI_Model {

    public function __construct() {
        parent::__construct();
        $this->load->database();
    }

    /**
     * Get or create a conversation session for the authenticated client.
     */
    public function get_or_create_conversation($conversation_id, $client_id, $question = '') {
        $query = $this->db->get_where('conversations', array(
            'conversation_id' => $conversation_id,
            'client_id'       => $client_id
        ));

        if ($query->num_rows() === 0) {
            $data = array(
                'conversation_id' => $conversation_id,
                'client_id'       => $client_id,
                'question'        => !empty($question) ? $question : 'Initial inquiry',
                'answer_payload'  => json_encode(array('status' => 'pending')),
                'confidence'      => 0.000,
                'created_at'      => date('Y-m-d H:i:s')
            );
            $this->db->insert('conversations', $data);
        }
        return $conversation_id;
    }

    /**
     * Save a message turn under a conversation with client ownership.
     */
    public function save_message($message_id, $conversation_id, $client_id, $role, $content, $confidence = NULL, $escalated = 0, $raw_payload = NULL) {
        // Enforce conversation ownership
        $conv = $this->db->get_where('conversations', array(
            'conversation_id' => $conversation_id,
            'client_id'       => $client_id
        ))->row();

        if (!$conv) {
            log_message('error', "IDOR attempt: Client {$client_id} cannot save to conversation {$conversation_id}");
            return FALSE;
        }

        // Deduplication check
        $exists = $this->db->get_where('messages', array('message_id' => $message_id))->num_rows();
        if ($exists > 0) {
            return TRUE;
        }

        $data = array(
            'message_id'      => $message_id,
            'conversation_id' => $conversation_id,
            'role'            => $role,
            'content'         => $content,
            'confidence'      => $confidence,
            'escalated'       => $escalated ? 1 : 0,
            'raw_payload'     => is_array($raw_payload) ? json_encode($raw_payload) : $raw_payload,
            'created_at'      => date('Y-m-d H:i:s')
        );

        return $this->db->insert('messages', $data);
    }

    /**
     * Retrieve conversation history strictly for the authenticated client.
     */
    public function get_client_history($client_id, $limit = 30) {
        $this->db->select('m.message_id, m.conversation_id, m.role, m.content, m.confidence, m.escalated, m.raw_payload, m.created_at, c.client_id');
        $this->db->from('messages m');
        $this->db->join('conversations c', 'c.conversation_id = m.conversation_id');
        $this->db->where('c.client_id', $client_id);
        $this->db->order_by('m.created_at', 'ASC');
        $this->db->limit((int)$limit);

        return $this->db->get()->result_array();
    }

    /**
     * Save feedback (thumbs up / down) with client ownership and deduplication.
     */
    public function record_feedback($message_id, $client_id, $rating, $comment = NULL) {
        // Enforce that message belongs to a conversation owned by this client
        $this->db->select('m.message_id, m.conversation_id');
        $this->db->from('messages m');
        $this->db->join('conversations c', 'c.conversation_id = m.conversation_id');
        $this->db->where('m.message_id', $message_id);
        $this->db->where('c.client_id', $client_id);
        $msg = $this->db->get()->row();

        if (!$msg) {
            return array('success' => FALSE, 'error' => 'Message not found or unauthorized.');
        }

        // Check if feedback already exists for this message
        $existing = $this->db->get_where('feedback', array('message_id' => $message_id))->row();

        if ($existing) {
            // Update existing feedback rating rather than creating duplicates
            $this->db->where('message_id', $message_id);
            $this->db->update('feedback', array(
                'rating'     => $rating,
                'comment'    => $comment,
                'created_at' => date('Y-m-d H:i:s')
            ));
            return array('success' => TRUE, 'action' => 'updated');
        }

        // Insert new feedback
        $this->db->insert('feedback', array(
            'message_id'      => $message_id,
            'conversation_id' => $msg->conversation_id,
            'rating'          => $rating,
            'comment'         => $comment,
            'created_at'      => date('Y-m-d H:i:s')
        ));

        return array('success' => TRUE, 'action' => 'created');
    }

    /**
     * Retrieve escalations for authenticated client only.
     */
    public function get_client_escalations($client_id, $limit = 20) {
        $this->db->select('ticket_id, conversation_id, client_id, question, reason, confidence, status, created_at, resolved_at');
        $this->db->from('escalations');
        $this->db->where('client_id', $client_id);
        $this->db->order_by('created_at', 'DESC');
        $this->db->limit((int)$limit);

        return $this->db->get()->result_array();
    }
}
