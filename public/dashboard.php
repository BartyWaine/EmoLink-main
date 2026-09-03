<?php
// /public/dashboard.php
require_once __DIR__ . '/../app/db.php';
require_once __DIR__ . '/../app/auth.php';

require_login();
$user_id = get_current_user_id();

// Handle toggle visibility
if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['action']) && $_POST['action'] === 'toggle_visibility') {
    $family_id = $_POST['family_id'] ?? null;
    $new_visibility = $_POST['visibility'] === 'private' ? 'private' : 'shared';
    if ($family_id) {
        $stmt = $pdo->prepare("UPDATE family_members SET visibility = ? WHERE family_id = ? AND user_id = ?");
        $stmt->execute([$new_visibility, $family_id, $user_id]);
    }
    header('Location: dashboard.php');
    exit;
}

// Fetch current user details
$stmt = $pdo->prepare("SELECT name FROM users WHERE id = ?");
$stmt->execute([$user_id]);
$user = $stmt->fetch();

// Fetch families the user belongs to and their tree progress
$stmt = $pdo->prepare("
    SELECT f.id, f.family_name, f.invite_code, fm.role, fm.visibility,
           COALESCE(tp.points, 0) as points, COALESCE(tp.level, 1) as level
    FROM families f
    JOIN family_members fm ON f.id = fm.family_id
    LEFT JOIN tree_progress tp ON f.id = tp.family_id
    WHERE fm.user_id = ?
");
$stmt->execute([$user_id]);
$families = $stmt->fetchAll();

// Mood color map
$mood_colors = [
    'happy' => '#facc15',
    'okay' => '#a3e635',
    'sad' => '#60a5fa',
    'angry' => '#f87171',
    'anxious' => '#c084fc'
];
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Dashboard - EmoLink</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500;9..144,600;9..144,700&family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="assets/style.css">
    <style>
        .member-list {
            list-style-type: none;
            padding: 0;
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 1rem;
        }
        .member-card {
            background-color: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 0.5rem;
            padding: 1rem;
            display: flex;
            flex-direction: column;
            gap: 0.75rem;
        }
        .member-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .badge {
            background-color: var(--border-color);
            color: var(--text-muted);
            padding: 0.25rem 0.5rem;
            border-radius: 9999px;
            font-size: 0.75rem;
            text-transform: uppercase;
            font-weight: bold;
        }
        .mood-badge {
            padding: 0.25rem 0.5rem;
            border-radius: 0.375rem;
            font-size: 0.875rem;
            font-weight: 500;
            color: #000;
            display: inline-block;
        }
        .journal-preview {
            font-size: 0.875rem;
            color: var(--text-muted);
            background-color: var(--bg-color);
            padding: 0.5rem;
            border-radius: 0.375rem;
            font-style: italic;
        }
        .actions-bar {
            display: flex;
            gap: 0.5rem;
            margin-top: 1rem;
            align-items: center;
        }
        .dot {
            height: 12px;
            width: 12px;
            border-radius: 50%;
            display: inline-block;
            margin-right: 4px;
        }
        .dot.open { background-color: var(--success-color); }
        .dot.closed { background-color: var(--text-muted); }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>Welcome, <?= htmlspecialchars($user['name']) ?></h2>
            <a href="logout.php" class="btn btn-outline" style="width: auto;">Log Out</a>
        </div>

        <?php if (empty($families)): ?>
            <div class="card" style="max-width: 100%;">
                <h3 class="mb-4">You are not part of any family yet.</h3>
                <p>Join or create a family to start connecting.</p>
                <a href="family.php" class="btn mt-3" style="max-width: 200px;">Setup Family</a>
            </div>
        <?php else: ?>
            <!-- Join/Create Another Family button removed to enforce single-family restriction -->
            
            <?php foreach ($families as $family): ?>
                <div class="card" style="max-width: 100%; margin-bottom: 2rem;">
                    <div class="family-info" style="display: flex; justify-content: space-between; align-items: flex-start;">
                        <div>
                            <h3><?= htmlspecialchars($family['family_name']) ?></h3>
                            <p><strong>Invite Code:</strong> <span style="font-family: monospace; font-size: 1.1rem;"><?= htmlspecialchars($family['invite_code']) ?></span></p>
                            <p><strong>Your Role:</strong> <?= htmlspecialchars(ucfirst($family['role'])) ?></p>
                        </div>
                        <div style="text-align: right;">
                            <form method="POST" style="display: inline-block;">
                                <input type="hidden" name="action" value="toggle_visibility">
                                <input type="hidden" name="family_id" value="<?= $family['id'] ?>">
                                <input type="hidden" name="visibility" value="<?= $family['visibility'] === 'shared' ? 'private' : 'shared' ?>">
                                <button type="submit" class="btn-outline" style="padding: 0.25rem 0.5rem; font-size: 0.875rem;">
                                    Make data <?= $family['visibility'] === 'shared' ? 'Private' : 'Shared' ?>
                                </button>
                            </form>
                            <p style="font-size: 0.85rem; margin-top: 0.25rem; font-weight: 700; color: <?= $family['visibility'] === 'private' ? '#D32F2F' : '#2E7D32' ?>;">
                                Currently: <?= htmlspecialchars(ucfirst($family['visibility'])) ?>
                            </p>
                        </div>
                    </div>

                    <div class="actions-bar" style="margin-bottom: 2rem;">
                        <a href="checkin.php?family_id=<?= $family['id'] ?>" class="btn" style="width: auto;">Check In (Mood/Journal)</a>
                        <?php
                            $door_stmt = $pdo->prepare("SELECT status FROM open_door_signals WHERE user_id = ? AND family_id = ? ORDER BY created_at DESC LIMIT 1");
                            $door_stmt->execute([$user_id, $family['id']]);
                            $current_door = $door_stmt->fetchColumn() ?: 'closed';
                            $door_color = ($current_door === 'open') ? 'var(--success-color)' : 'var(--text-muted)';
                            $door_bg = ($current_door === 'open') ? 'rgba(127, 163, 123, 0.1)' : 'transparent';
                        ?>
                        <form action="open_door.php" method="POST" style="margin: 0;" onsubmit="handleOpenDoor(event, this)">
                            <input type="hidden" name="ajax" value="1">
                            <input type="hidden" name="family_id" value="<?= $family['id'] ?>">
                            <button type="submit" class="btn-outline" style="width: auto; transition: all 0.2s ease; border-color: <?= $door_color ?>; color: <?= $door_color ?>; background-color: <?= $door_bg ?>;">I'm available to talk</button>
                        </form>
                        <a href="topics.php?family_id=<?= $family['id'] ?>" class="btn" style="width: auto; background-color: #8b5cf6;">Get AI Topics</a>
                    </div>
                    
                    <?php
                        $points_into_level = $family['points'] % 50;
                        $percent = ($points_into_level / 50) * 100;
                        
                        $icon = '🌱';
                        if ($family['level'] == 2) $icon = '🌿';
                        elseif ($family['level'] == 3) $icon = '🪴';
                        elseif ($family['level'] == 4) $icon = '🌳';
                        elseif ($family['level'] >= 5) $icon = '🌲';
                    ?>
                    
                    <div class="growth-tree-card">
                        <div class="tree-header">
                            <span class="tree-icon"><?= $icon ?></span>
                            <div>
                                <div class="tree-level">Level <?= $family['level'] ?></div>
                                <div class="tree-points"><?= $family['points'] ?> total points</div>
                            </div>
                        </div>
                        <div class="progress-bar-bg">
                            <div class="progress-bar-fill" style="width: <?= $percent ?>%;"></div>
                        </div>
                        <div class="progress-text"><?= $points_into_level ?> / 50 to next level</div>
                    </div>

                    <h4 class="mt-4 mb-3">Family Pulse</h4>
                    <?php
                    // Family Pulse: latest entry per member, respecting privacy
                    $stmt = $pdo->prepare("
                        SELECT u.id as user_id, u.name, fm.role, fm.visibility,
                               (SELECT status FROM open_door_signals o WHERE o.user_id = u.id AND o.family_id = fm.family_id ORDER BY created_at DESC LIMIT 1) as open_door,
                               CASE WHEN fm.visibility = 'shared' OR u.id = ? THEN (SELECT mood FROM moods m WHERE m.user_id = u.id AND m.family_id = fm.family_id ORDER BY created_at DESC LIMIT 1) ELSE NULL END as latest_mood,
                               CASE WHEN fm.visibility = 'shared' OR u.id = ? THEN (SELECT entry_text FROM journal_entries j WHERE j.user_id = u.id AND j.family_id = fm.family_id ORDER BY created_at DESC LIMIT 1) ELSE NULL END as latest_journal
                        FROM family_members fm
                        JOIN users u ON u.id = fm.user_id
                        WHERE fm.family_id = ?
                        ORDER BY u.name ASC
                    ");
                    $stmt->execute([$user_id, $user_id, $family['id']]);
                    $members = $stmt->fetchAll();
                    ?>
                    
                    <div class="member-list">
                        <?php foreach ($members as $member): ?>
                            <div class="member-card" <?= $member['user_id'] == $user_id ? 'style="border-color: var(--primary-color); background-color: #f8faff;"' : '' ?>>
                                <div class="member-header">
                                    <div style="display: flex; align-items: center;">
                                        <?php $door_status = $member['open_door'] ?? 'closed'; ?>
                                        <span id="door-dot-<?= $family['id'] ?>-<?= $member['user_id'] ?>" class="dot <?= $door_status ?>" title="Door is <?= $door_status ?>"></span>
                                        <strong><?= htmlspecialchars($member['name']) ?><?= $member['user_id'] == $user_id ? ' <span style="color: var(--primary-color); font-weight: normal;">(You)</span>' : '' ?></strong>
                                    </div>
                                    <span class="badge"><?= htmlspecialchars($member['role']) ?></span>
                                </div>
                                
                                <div>
                                    <?php if ($member['latest_mood']): ?>
                                        <span class="mood-badge" style="background-color: <?= $mood_colors[$member['latest_mood']] ?? '#ddd' ?>;">
                                            <?= ucfirst(htmlspecialchars($member['latest_mood'])) ?>
                                        </span>
                                    <?php elseif ($member['visibility'] === 'private' && $member['user_id'] != $user_id): ?>
                                        <span class="text-muted" style="font-size: 0.875rem;">(Hidden)</span>
                                    <?php else: ?>
                                        <span class="text-muted" style="font-size: 0.875rem;">No mood yet</span>
                                    <?php endif; ?>
                                </div>

                                <?php if ($member['latest_journal']): ?>
                                    <div class="journal-preview">
                                        "<?= htmlspecialchars(mb_strimwidth($member['latest_journal'], 0, 60, "...")) ?>"
                                    </div>
                                <?php endif; ?>
                                
                                <?php if ($member['user_id'] == $user_id && $member['visibility'] === 'private'): ?>
                                    <div style="font-size: 0.75rem; color: var(--error-color); margin-top: auto;">
                                        (Your entries are hidden from others)
                                    </div>
                                <?php endif; ?>
                            </div>
                        <?php endforeach; ?>
                    </div>
                </div>
            <?php endforeach; ?>
        <?php endif; ?>
    </div>
    
    <script>
    async function handleOpenDoor(e, form) {
        e.preventDefault();
        const btn = form.querySelector('button');
        
        btn.style.opacity = '0.7';

        try {
            const formData = new FormData(form);
            const response = await fetch(form.action, {
                method: 'POST',
                body: formData
            });
            
            if (response.ok) {
                const data = await response.json();
                if (data.status === 'success') {
                    const familyId = form.querySelector('input[name="family_id"]').value;
                    const dot = document.getElementById(`door-dot-${familyId}-<?= $user_id ?>`);
                    
                    if (data.new_status === 'open') {
                        btn.style.borderColor = 'var(--success-color)';
                        btn.style.color = 'var(--success-color)';
                        btn.style.backgroundColor = 'rgba(127, 163, 123, 0.1)';
                        if (dot) {
                            dot.className = 'dot open';
                            dot.title = 'Door is open';
                        }
                    } else {
                        btn.style.borderColor = 'var(--text-muted)';
                        btn.style.color = 'var(--text-muted)';
                        btn.style.backgroundColor = 'transparent';
                        if (dot) {
                            dot.className = 'dot closed';
                            dot.title = 'Door is closed';
                        }
                    }
                }
            }
        } catch (err) {
            console.error("Failed to toggle door", err);
        } finally {
            btn.style.opacity = '1';
        }
    }
    </script>
</body>
</html>
