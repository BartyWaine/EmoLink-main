<?php
// /app/auth.php

// Check if the current user is logged in
function is_logged_in() {
    return isset($_SESSION['user_id']);
}

// Get current user ID (returns null if not logged in)
function get_current_user_id() {
    return is_logged_in() ? $_SESSION['user_id'] : null;
}

// Redirect to login page if not logged in
function require_login() {
    if (!is_logged_in()) {
        header('Location: login.php');
        exit;
    }
}

// Ensure the current user is a member of the given family
function require_family_member($pdo, $family_id, $user_id) {
    $stmt = $pdo->prepare('SELECT role, visibility FROM family_members WHERE family_id = ? AND user_id = ?');
    $stmt->execute([$family_id, $user_id]);
    $membership = $stmt->fetch();
    if (!$membership) {
        http_response_code(403);
        exit('Not a member of this family.');
    }
    return $membership;
}
