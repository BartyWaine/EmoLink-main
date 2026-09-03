<?php
// /public/checkin.php
require_once __DIR__ . '/../app/db.php';
require_once __DIR__ . '/../app/auth.php';

require_login();
$user_id = get_current_user_id();

$family_id = $_GET['family_id'] ?? ($_POST['family_id'] ?? null);

if (!$family_id) {
    http_response_code(400);
    die('Family ID required. Please navigate from the dashboard.');
}

// Guard: verify membership
$membership = require_family_member($pdo, $family_id, $user_id);

$error = '';

$valid_moods = ['happy', 'okay', 'sad', 'angry', 'anxious'];
$mood_colors = [
    'happy' => '#facc15',
    'okay' => '#a3e635',
    'sad' => '#60a5fa',
    'angry' => '#f87171',
    'anxious' => '#c084fc'
];

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $mood = $_POST['mood'] ?? '';
    $journal = trim($_POST['journal'] ?? '');
    
    if (!in_array($mood, $valid_moods)) {
        $error = 'Please select a valid mood.';
    } else {
        try {
            $pdo->beginTransaction();

            $color = $mood_colors[$mood];
            $stmt = $pdo->prepare("INSERT INTO moods (family_id, user_id, mood, color) VALUES (?, ?, ?, ?)");
            $stmt->execute([$family_id, $user_id, $mood, $color]);

            if (!empty($journal)) {
                $stmt = $pdo->prepare("INSERT INTO journal_entries (family_id, user_id, entry_text) VALUES (?, ?, ?)");
                $stmt->execute([$family_id, $user_id, $journal]);
            }

            // Award points for check-in
            award_family_points($pdo, $family_id, 10);

            $pdo->commit();
            header('Location: dashboard.php');
            exit;
        } catch (Exception $e) {
            $pdo->rollBack();
            $error = 'Failed to save check-in. Please try again.';
        }
    }
}
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Check-in - EmoLink</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500;9..144,600;9..144,700&family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="assets/style.css">
    <style>
        .mood-options {
            display: flex;
            gap: 1rem;
            flex-wrap: wrap;
            margin-bottom: 1.5rem;
        }
        .mood-option {
            flex: 1;
            min-width: 80px;
            text-align: center;
            padding: 1rem;
            border: 2px solid var(--border-color);
            border-radius: 0.5rem;
            cursor: pointer;
            transition: all 0.2s;
            background-color: var(--card-bg);
            font-weight: 500;
        }
        .mood-option input[type="radio"] {
            display: none;
        }
        /* Style when checked */
        .mood-label:has(input[type="radio"]:checked) {
            border-color: var(--primary-color);
            box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.2);
            background-color: #f8faff;
        }
        
        .mood-label[data-mood="happy"] { border-bottom-color: #facc15; border-bottom-width: 4px; }
        .mood-label[data-mood="okay"] { border-bottom-color: #a3e635; border-bottom-width: 4px; }
        .mood-label[data-mood="sad"] { border-bottom-color: #60a5fa; border-bottom-width: 4px; }
        .mood-label[data-mood="angry"] { border-bottom-color: #f87171; border-bottom-width: 4px; }
        .mood-label[data-mood="anxious"] { border-bottom-color: #c084fc; border-bottom-width: 4px; }
        
        textarea {
            width: 100%;
            padding: 0.75rem;
            border: 1px solid var(--border-color);
            border-radius: 0.375rem;
            font-size: 1rem;
            resize: vertical;
            min-height: 120px;
            font-family: inherit;
        }
        textarea:focus {
            outline: none;
            border-color: var(--primary-color);
            box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.1);
        }
    </style>
</head>
<body>
    <div class="auth-container">
        <div class="card" style="max-width: 600px;">
            <h2>How are you feeling?</h2>
            
            <?php if ($error): ?>
                <div class="error-msg"><?= htmlspecialchars($error) ?></div>
            <?php endif; ?>

            <?php if ($membership['visibility'] === 'private'): ?>
                <div class="success-msg" style="background-color: #fffbeb; border-color: #fcd34d; color: #b45309;">
                    Note: Your visibility is currently set to Private. Your entries won't be seen by others.
                </div>
            <?php endif; ?>

            <form method="POST">
                <input type="hidden" name="family_id" value="<?= htmlspecialchars($family_id) ?>">
                
                <div class="mood-options">
                    <?php foreach ($valid_moods as $vm): ?>
                        <label class="mood-option mood-label" data-mood="<?= $vm ?>">
                            <input type="radio" name="mood" value="<?= $vm ?>" required>
                            <?= ucfirst($vm) ?>
                        </label>
                    <?php endforeach; ?>
                </div>

                <div class="form-group">
                    <label>Journal Entry (Optional)</label>
                    <textarea name="journal" placeholder="Write down any thoughts, events, or details about your day..."></textarea>
                </div>
                
                <div id="crisis-resource" style="display: none; background-color: var(--msg-bg-error); padding: 1rem; border-radius: 12px; margin-bottom: 1rem; font-size: 0.85rem; color: #b45309;">
                    <strong>Your well-being matters.</strong> If you're feeling overwhelmed, please reach out to a trusted adult or a <a href="https://findahelpline.com/" target="_blank" style="color: var(--primary-color); font-weight: bold; text-decoration: underline;">Crisis Resource</a>. You are not alone.
                </div>

                <button type="submit" class="mt-4">Save Check-in</button>
            </form>
            
            <div class="text-center mt-3">
                <a href="dashboard.php">Cancel & Return</a>
            </div>
        </div>
    </div>
    <script>
        document.querySelectorAll('input[name="mood"]').forEach(radio => {
            radio.addEventListener('change', (e) => {
                const crisisDiv = document.getElementById('crisis-resource');
                if (e.target.value === 'sad' || e.target.value === 'anxious') {
                    crisisDiv.style.display = 'block';
                } else {
                    crisisDiv.style.display = 'none';
                }
            });
        });
    </script>
</body>
</html>
