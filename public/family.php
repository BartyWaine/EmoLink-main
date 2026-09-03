<?php
// /public/family.php
require_once __DIR__ . '/../app/db.php';
require_once __DIR__ . '/../app/auth.php';

require_login();
$user_id = get_current_user_id();

$error = '';
$success = '';

// Helper to generate invite code
function generate_invite_code($length = 6) {
    $chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'; // No 0, O, 1, I
    $code = '';
    for ($i = 0; $i < $length; $i++) {
        $code .= $chars[random_int(0, strlen($chars) - 1)];
    }
    return $code;
}

// Check if user is already in a family
$stmt = $pdo->prepare("SELECT COUNT(*) FROM family_members WHERE user_id = ?");
$stmt->execute([$user_id]);
$family_count = $stmt->fetchColumn();

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    if ($family_count > 0) {
        $error = "You are already a member of a family. Accounts are restricted to a single family.";
    } else {
        $action = $_POST['action'] ?? '';
    $role = $_POST['role'] ?? 'teen'; // default to teen, should be validated
    if (!in_array($role, ['parent', 'teen'])) {
        $role = 'teen';
    }

    if ($action === 'create') {
        $family_name = trim($_POST['family_name'] ?? '');
        if (empty($family_name)) {
            $error = 'Family name is required.';
        } else {
            try {
                $pdo->beginTransaction();

                // Loop to ensure unique invite code
                $invite_code = '';
                $is_unique = false;
                $attempts = 0;
                while (!$is_unique && $attempts < 10) {
                    $invite_code = generate_invite_code();
                    $stmt = $pdo->prepare("SELECT id FROM families WHERE invite_code = ?");
                    $stmt->execute([$invite_code]);
                    if (!$stmt->fetch()) {
                        $is_unique = true;
                    }
                    $attempts++;
                }

                if (!$is_unique) {
                    throw new Exception("Failed to generate a unique invite code.");
                }

                $stmt = $pdo->prepare("INSERT INTO families (family_name, invite_code) VALUES (?, ?)");
                $stmt->execute([$family_name, $invite_code]);
                $family_id = $pdo->lastInsertId();

                $stmt = $pdo->prepare("INSERT INTO family_members (family_id, user_id, role) VALUES (?, ?, ?)");
                $stmt->execute([$family_id, $user_id, $role]);

                $pdo->commit();
                header('Location: dashboard.php');
                exit;
            } catch (Exception $e) {
                $pdo->rollBack();
                $error = 'Error creating family: ' . $e->getMessage();
            }
        }
    } elseif ($action === 'join') {
        $invite_code = trim($_POST['invite_code'] ?? '');
        if (empty($invite_code)) {
            $error = 'Invite code is required.';
        } else {
            try {
                $pdo->beginTransaction();

                // Check if family exists
                $stmt = $pdo->prepare("SELECT id FROM families WHERE invite_code = ?");
                $stmt->execute([$invite_code]);
                $family = $stmt->fetch();

                if (!$family) {
                    throw new Exception("Invalid invite code. Family not found.");
                }

                $family_id = $family['id'];

                // Attempt to insert. Will throw exception if unique key (family_id, user_id) is violated
                $stmt = $pdo->prepare("INSERT INTO family_members (family_id, user_id, role) VALUES (?, ?, ?)");
                $stmt->execute([$family_id, $user_id, $role]);

                $pdo->commit();
                header('Location: dashboard.php');
                exit;
            } catch (PDOException $e) {
                $pdo->rollBack();
                // Check if it's a unique constraint violation (duplicate entry)
                if ($e->getCode() == 23000) {
                    $error = 'You are already a member of this family.';
                } else {
                    $error = 'Database error joining family.';
                }
            } catch (Exception $e) {
                $pdo->rollBack();
                $error = $e->getMessage();
            }
        }
        }
    }
}
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Family Setup - EmoLink</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500;9..144,600;9..144,700&family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="assets/style.css">
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>EmoLink</h2>
            <a href="logout.php" class="btn btn-outline" style="width: auto;">Log Out</a>
        </div>
        
        <?php if ($error): ?>
            <div class="error-msg"><?= htmlspecialchars($error) ?></div>
        <?php endif; ?>

        <?php if ($family_count > 0): ?>
            <div class="card" style="max-width: 100%;">
                <h3>You are already in a family.</h3>
                <p>EmoLink currently restricts accounts to a single family connection.</p>
            </div>
        <?php else: ?>
            <div style="display: flex; gap: 2rem; flex-wrap: wrap;">
            <!-- Create Family -->
            <div class="card" style="flex: 1; min-width: 300px;">
                <h2>Create a Family</h2>
                <form method="POST">
                    <input type="hidden" name="action" value="create">
                    <div class="form-group">
                        <label>Family Name</label>
                        <input type="text" name="family_name" required placeholder="e.g., The Smiths">
                    </div>
                    <div class="form-group">
                        <label>Your Role</label>
                        <select name="role">
                            <option value="parent">Parent</option>
                            <option value="teen">Teen</option>
                        </select>
                    </div>
                    <button type="submit">Create Family</button>
                </form>
            </div>

            <!-- Join Family -->
            <div class="card" style="flex: 1; min-width: 300px;">
                <h2>Join a Family</h2>
                <form method="POST">
                    <input type="hidden" name="action" value="join">
                    <div class="form-group">
                        <label>Invite Code</label>
                        <input type="text" name="invite_code" required placeholder="Enter 6-8 char code">
                    </div>
                    <div class="form-group">
                        <label>Your Role</label>
                        <select name="role">
                            <option value="teen">Teen</option>
                            <option value="parent">Parent</option>
                        </select>
                    </div>
                    <button type="submit">Join Family</button>
                </form>
            </div>
        </div>
        <?php endif; ?>
        <div class="text-center mt-4">
            <a href="dashboard.php">Go to Dashboard</a>
        </div>
    </div>
</body>
</html>
