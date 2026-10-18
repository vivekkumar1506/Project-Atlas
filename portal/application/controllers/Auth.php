<?php
defined('BASEPATH') OR exit('No direct script access allowed');

class Auth extends CI_Controller {

    public function __construct() {
        parent::__construct();
        $this->load->library('session');
    }

    /**
     * Switch client context for testing entitlements (C-01, C-02, C-03).
     */
    public function switch_client($client_id = 'C-01') {
        $allowed = array(
            'C-01' => 'Northwind Utilities (Purchased: R-101, R-103)',
            'C-02' => 'Blue Delta Infra (Purchased: R-103 only)',
            'C-03' => 'Gamma Analytics Corp (Purchased: All)'
        );

        if (!isset($allowed[$client_id])) {
            $client_id = 'C-01';
        }

        $this->session->set_userdata(array(
            'client_id'   => $client_id,
            'client_name' => $allowed[$client_id],
            'logged_in'   => TRUE
        ));

        redirect('chat');
    }

    public function logout() {
        $this->session->sess_destroy();
        redirect('chat');
    }
}
