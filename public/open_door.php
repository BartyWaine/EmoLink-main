<?php
// /public/open_door.php
require_once __DIR__ . '/../app/db.php';
require_once __DIR__ . '/../app/auth.php';

require_login();
$user_id = get_current_user_id();

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $family_id = $_POST['family_id'] ?? null;
    
    if (!$family_id) {
        http_response_code(400);
        die('Family ID required.');
    }

    // Guard: verify membership
    require_family_member($pdo, $family_id, $user_id);

    // Get current status
    $stmt = $pdo->prepare("SELECT status FROM open_door_signals WHERE family_id = ? AND user_id = ?");
    $stmt->execute([$family_id, $user_id]);
    $signal = $stmt->fetch();

    $new_status = 'open';
    if ($signal) {
        $new_status = $signal['status'] === 'open' ? 'closed' : 'open';
        $stmt = $pdo->prepare("UPDATE open_door_signals SET status = ?, created_at = CURRENT_TIMESTAMP WHERE family_id = ? AND user_id = ?");
        $stmt->execute([$new_status, $family_id, $user_id]);
    } else {
        $stmt = $pdo->prepare("INSERT INTO open_door_signals (family_id, user_id, status) VALUES (?, ?, ?)");
        $stmt->execute([$family_id, $user_id, $new_status]);
    }
    if (isset($_POST['ajax'])) {
        header('Content-Type: application/json');
        echo json_encode(['status' => 'success', 'new_status' => $new_status]);
        exit;
    }
}

header('Location: dashboard.php');
exit;
