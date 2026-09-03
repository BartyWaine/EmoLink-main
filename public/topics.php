<?php
require_once __DIR__ . '/../app/db.php';
require_once __DIR__ . '/../app/auth.php';

require_login();
$user_id = get_current_user_id();

$family_id = $_GET['family_id'] ?? ($_POST['family_id'] ?? null);

if (!$family_id) {
    http_response_code(400);
    die('Family ID required. Please navigate from the dashboard.');
}

$membership = require_family_member($pdo, $family_id, $user_id);

$error = '';
$empty_msg = '';
$is_loading = false;
$ai_status = [];
$crisis_alerts = [];
$dynamics = null;
$predictions = [];
$topic_effectiveness = [];

if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['action'])) {
    if ($_POST['action'] === 'generate') {
        $ch = curl_init('http://127.0.0.1:8001/generate-topics');
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
        curl_setopt($ch, CURLOPT_POST, true);
        curl_setopt($ch, CURLOPT_HTTPHEADER, ['Content-Type: application/json']);
        curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode(['family_id' => (int)$family_id, 'use_ensemble' => true]));
        curl_setopt($ch, CURLOPT_TIMEOUT, 30);

        $response = curl_exec($ch);
        $curl_error = curl_error($ch);
        curl_close($ch);

        if ($response === false) {
            $error = "AI service offline — start it with uvicorn (Error: $curl_error)";
        } else {
            $result = json_decode($response, true);
            if (!$result) {
                $error = 'Invalid JSON response from AI service.';
            } else if ($result['status'] === 'empty') {
                $empty_msg = $result['message'];
            } else if ($result['status'] === 'error') {
                $error = 'AI Service Error: ' . htmlspecialchars($result['message']);
            } else if ($result['status'] === 'ok') {
                award_family_points($pdo, $family_id, 5);
                $ai_status = $result;
            }
        }

        if (isset($_POST['ajax'])) {
            header('Content-Type: application/json');
            echo json_encode([
                'success' => !$error && !$empty_msg,
                'error' => $error,
                'empty_msg' => $empty_msg,
                'ai_status' => $ai_status
            ]);
            exit;
        }
    }

    if ($_POST['action'] === 'topic_feedback' && isset($_POST['topic_id']) && isset($_POST['feedback_type'])) {
        $topic_id = (int)$_POST['topic_id'];
        $feedback_type = $_POST['feedback_type'];

        $ch = curl_init("http://127.0.0.1:8001/topic-feedback");
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
        curl_setopt($ch, CURLOPT_POST, true);
        curl_setopt($ch, CURLOPT_HTTPHEADER, ['Content-Type: application/json']);
        curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode([
            'topic_id' => $topic_id,
            'user_id' => $user_id,
            'feedback_type' => $feedback_type
        ]));
        curl_setopt($ch, CURLOPT_TIMEOUT, 10);
        curl_exec($ch);
        curl_close($ch);

        if (isset($_POST['ajax'])) {
            header('Content-Type: application/json');
            echo json_encode(['success' => true]);
            exit;
        }

        header('Location: topics.php?family_id=' . $family_id);
        exit;
    }

    if ($_POST['action'] === 'analyze_dynamics') {
        $ch = curl_init("http://127.0.0.1:8001/analyze-dynamics");
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
        curl_setopt($ch, CURLOPT_POST, true);
        curl_setopt($ch, CURLOPT_HTTPHEADER, ['Content-Type: application/json']);
        curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode(['family_id' => (int)$family_id]));
        curl_setopt($ch, CURLOPT_TIMEOUT, 15);
        $response = curl_exec($ch);
        curl_close($ch);

        if ($response) {
            $result = json_decode($response, true);
            if ($result['status'] === 'ok') {
                $_SESSION['dynamics_result'] = $result;
            }
        }

        if (isset($_POST['ajax'])) {
            header('Content-Type: application/json');
            echo $response ?: json_encode(['status' => 'error']);
            exit;
        }
    }

    if ($_POST['action'] === 'resolve_alert' && isset($_POST['alert_id'])) {
        $alert_id = (int)$_POST['alert_id'];
        $ch = curl_init("http://127.0.0.1:8001/resolve-crisis/" . $alert_id);
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
        curl_setopt($ch, CURLOPT_POST, true);
        curl_setopt($ch, CURLOPT_TIMEOUT, 10);
        curl_exec($ch);
        curl_close($ch);

        header('Location: topics.php?family_id=' . $family_id);
        exit;
    }
}

$ch = curl_init("http://127.0.0.1:8001/get-crisis-alerts/" . $family_id);
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
curl_setopt($ch, CURLOPT_TIMEOUT, 10);
$response = curl_exec($ch);
if ($response) {
    $crisis_data = json_decode($response, true);
    if ($crisis_data['status'] === 'ok') {
        $crisis_alerts = $crisis_data['alerts'];
    }
}
curl_close($ch);

$ch = curl_init("http://127.0.0.1:8001/get-dynamics/" . $family_id);
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
curl_setopt($ch, CURLOPT_TIMEOUT, 10);
$response = curl_exec($ch);
if ($response) {
    $dynamics_data = json_decode($response, true);
    if ($dynamics_data['status'] === 'ok') {
        $dynamics = $dynamics_data['dynamics'];
    }
}
curl_close($ch);

$ch = curl_init("http://127.0.0.1:8001/predict-moods");
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
curl_setopt($ch, CURLOPT_POST, true);
curl_setopt($ch, CURLOPT_HTTPHEADER, ['Content-Type: application/json']);
curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode(['family_id' => (int)$family_id]));
curl_setopt($ch, CURLOPT_TIMEOUT, 15);
$response = curl_exec($ch);
if ($response) {
    $pred_data = json_decode($response, true);
    if ($pred_data['status'] === 'ok') {
        $predictions = $pred_data['predictions'];
    }
}
curl_close($ch);

$ch = curl_init("http://127.0.0.1:8001/topic-effectiveness/" . $family_id);
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
curl_setopt($ch, CURLOPT_TIMEOUT, 10);
$response = curl_exec($ch);
if ($response) {
    $eff_data = json_decode($response, true);
    if ($eff_data['status'] === 'ok') {
        $topic_effectiveness = $eff_data['effectiveness'];
    }
}
curl_close($ch);

$stmt = $pdo->prepare("SELECT topic_text, based_on, created_at, id FROM ai_topics WHERE family_id = ? ORDER BY created_at DESC LIMIT 5");
$stmt->execute([$family_id]);
$topics_from_db = $stmt->fetchAll();

$stmt = $pdo->prepare("SELECT summary FROM ai_context WHERE family_id = ?");
$stmt->execute([$family_id]);
$context = $stmt->fetch();
$summary = $context ? $context['summary'] : '';

$family_stmt = $pdo->prepare("SELECT family_name FROM families WHERE id = ?");
$family_stmt->execute([$family_id]);
$family = $family_stmt->fetch();
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>AI Insights - EmoLink</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500;9..144,600;9..144,700&family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="assets/style.css">
    <style>
        .topic-card {
            background-color: var(--card-bg);
            border: 1px solid var(--border-color);
            border-left: 4px solid var(--primary-color);
            border-radius: 0.5rem;
            padding: 1.5rem;
            margin-bottom: 1rem;
        }
        .topic-text {
            font-size: 1.125rem;
            font-weight: 500;
            color: var(--text-main);
            margin-bottom: 0.5rem;
        }
        .based-on {
            font-size: 0.875rem;
            color: var(--text-muted);
            font-style: italic;
        }
        .summary-box {
            background-color: #f0fdf4;
            border: 1px solid #bbf7d0;
            padding: 1rem;
            border-radius: 0.5rem;
            margin-bottom: 2rem;
            color: #166534;
        }
        .spinner {
            border: 3px solid rgba(255,255,255,0.3);
            border-top: 3px solid #fff;
            border-radius: 50%;
            width: 16px;
            height: 16px;
            animation: spin 1s linear infinite;
            display: inline-block;
            vertical-align: middle;
            margin-left: 8px;
            display: none;
        }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }

        .alert-card {
            background-color: #fef2f2;
            border: 1px solid #fecaca;
            border-left: 4px solid #ef4444;
            padding: 1rem;
            border-radius: 0.5rem;
            margin-bottom: 1rem;
        }
        .alert-card.low { border-left-color: #f59e0b; background-color: #fffbeb; }
        .alert-card.medium { border-left-color: #f97316; background-color: #fff7ed; }
        .alert-card.high { border-left-color: #ef4444; background-color: #fef2f2; }
        .alert-card.critical { border-left-color: #dc2626; background-color: #fee2e2; }

        .dynamics-card {
            background-color: var(--card-bg);
            border: 1px solid var(--border-color);
            padding: 1.5rem;
            border-radius: 0.5rem;
            margin-bottom: 1rem;
        }

        .prediction-badge {
            display: inline-flex;
            align-items: center;
            padding: 0.25rem 0.75rem;
            border-radius: 9999px;
            font-size: 0.875rem;
            font-weight: 500;
        }
        .prediction-badge.improving { background-color: #dcfce7; color: #166534; }
        .prediction-badge.declining { background-color: #fee2e2; color: #991b1b; }
        .prediction-badge.stable { background-color: #f3f4f6; color: #374151; }

        .tabs {
            display: flex;
            gap: 0.5rem;
            margin-bottom: 1.5rem;
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 0.5rem;
        }
        .tab-btn {
            padding: 0.5rem 1rem;
            border: none;
            background: none;
            cursor: pointer;
            font-size: 0.95rem;
            color: var(--text-muted);
            border-radius: 0.375rem;
            transition: all 0.2s;
        }
        .tab-btn.active {
            background-color: var(--primary-color);
            color: white;
        }
        .tab-content { display: none; }
        .tab-content.active { display: block; }

        .insight-tag {
            display: inline-block;
            background-color: #e0e7ff;
            color: #3730a3;
            padding: 0.25rem 0.75rem;
            border-radius: 9999px;
            font-size: 0.8rem;
            margin: 0.25rem;
        }

        .feedback-btns {
            display: flex;
            gap: 0.5rem;
            margin-top: 1rem;
        }
        .feedback-btn {
            padding: 0.375rem 0.75rem;
            border: 1px solid var(--border-color);
            background: var(--card-bg);
            border-radius: 0.375rem;
            font-size: 0.8rem;
            cursor: pointer;
            transition: all 0.2s;
        }
        .feedback-btn:hover { background-color: var(--border-color); }
        .feedback-btn.discussed { border-color: #22c55e; color: #166534; }
        .feedback-btn.helpful { border-color: #3b82f6; color: #1d4ed8; }
        .feedback-btn.not-helpful { border-color: #ef4444; color: #dc2626; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>AI Insights</h2>
            <a href="dashboard.php" class="btn btn-outline" style="width: auto;">Dashboard</a>
        </div>

        <?php if (!empty($crisis_alerts)): ?>
            <div style="margin-bottom: 2rem;">
                <h3 style="color: #dc2626; margin-bottom: 1rem;">
                    <svg style="width: 20px; height: 20px; vertical-align: middle; margin-right: 8px;" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd"/></svg>
                    Crisis Alerts (<?= count($crisis_alerts) ?>)
                </h3>
                <?php foreach ($crisis_alerts as $alert): ?>
                    <div class="alert-card <?= htmlspecialchars($alert['severity']) ?>">
                        <div style="display: flex; justify-content: space-between; align-items: start;">
                            <div>
                                <strong><?= htmlspecialchars($alert['user_name']) ?></strong>
                                <span style="font-size: 0.8rem; color: #666;">(<?= htmlspecialchars($alert['role']) ?>)</span>
                                <p style="margin: 0.5rem 0;"><?= htmlspecialchars($alert['message']) ?></p>
                                <span style="font-size: 0.75rem; color: #888;">
                                    <?= ucfirst($alert['alert_type']) ?> |
                                    Severity: <strong><?= strtoupper($alert['severity']) ?></strong>
                                </span>
                            </div>
                            <form method="POST" style="margin: 0;">
                                <input type="hidden" name="action" value="resolve_alert">
                                <input type="hidden" name="alert_id" value="<?= $alert['id'] ?>">
                                <button type="submit" style="padding: 0.25rem 0.75rem; font-size: 0.75rem; background: #dc2626; color: white; border: none; border-radius: 0.25rem; cursor: pointer;">Acknowledge</button>
                            </form>
                        </div>
                    </div>
                <?php endforeach; ?>
            </div>
        <?php endif; ?>

        <div class="tabs">
            <button class="tab-btn active" onclick="showTab('topics')">Topics</button>
            <button class="tab-btn" onclick="showTab('insights')">Family Insights</button>
            <button class="tab-btn" onclick="showTab('predictions')">Predictions</button>
        </div>

        <div id="tab-topics" class="tab-content active">
            <?php if ($error): ?>
                <div class="error-msg"><?= $error ?></div>
            <?php endif; ?>

            <?php if ($empty_msg): ?>
                <div class="card mb-4">
                    <h3 style="color: var(--text-main); margin-bottom: 0.5rem;">Not quite ready...</h3>
                    <p><?= htmlspecialchars($empty_msg) ?></p>
                    <a href="checkin.php?family_id=<?= $family_id ?>" class="btn mt-3" style="max-width: 200px;">Add Check-in</a>
                </div>
            <?php endif; ?>

            <?php if (!empty($ai_status)): ?>
                <div class="summary-box" style="margin-bottom: 1.5rem;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <strong>Topic Generation Complete</strong>
                            <?php if (!empty($ai_status['models_used'])): ?>
                                <p style="margin: 0.25rem 0 0 0; font-size: 0.85rem;">
                                    Models used: <?= implode(', ', array_map('ucfirst', $ai_status['models_used'])) ?>
                                    <?php if (!empty($ai_status['ensemble_used'])): ?>
                                        <span style="background: #dbeafe; padding: 0.1rem 0.4rem; border-radius: 4px; font-size: 0.75rem; margin-left: 0.5rem;">Ensemble Mode</span>
                                    <?php endif; ?>
                                </p>
                            <?php endif; ?>
                        </div>
                        <span style="font-size: 1.5rem;">✨</span>
                    </div>
                </div>
            <?php endif; ?>

            <form method="POST" style="margin-bottom: 2rem;" id="generate-form">
                <input type="hidden" name="action" value="generate">
                <input type="hidden" name="family_id" value="<?= htmlspecialchars($family_id) ?>">
                <button type="submit" id="generate-btn" style="max-width: 350px; padding: 1rem; font-size: 1.1rem; display: flex; align-items: center; justify-content: center; gap: 8px;">
                    <span>Generate AI Topics (Ensemble)</span>
                    <span class="spinner" id="spinner"></span>
                </button>
                <p class="text-muted mt-3" style="font-size: 0.875rem;">Uses multiple AI models for higher quality topics</p>
            </form>

            <?php if ($summary): ?>
                <div class="summary-box">
                    <strong>AI Context Summary:</strong><br>
                    <?= htmlspecialchars($summary) ?>
                </div>
            <?php endif; ?>

            <?php if ($topics_from_db): ?>
                <h3>Recent Topics</h3>
                <div class="mt-4">
                    <?php foreach ($topics_from_db as $topic): ?>
                        <div class="topic-card">
                            <div class="topic-text">"<?= htmlspecialchars($topic['topic_text']) ?>"</div>
                            <?php if ($topic['based_on']): ?>
                                <div class="based-on">&mdash; <?= htmlspecialchars($topic['based_on']) ?></div>
                            <?php endif; ?>
                            <div class="feedback-btns">
                                <form method="POST" style="display: inline;">
                                    <input type="hidden" name="action" value="topic_feedback">
                                    <input type="hidden" name="topic_id" value="<?= $topic['id'] ?>">
                                    <input type="hidden" name="feedback_type" value="discussed">
                                    <button type="submit" class="feedback-btn discussed">✓ We Discussed This</button>
                                </form>
                                <form method="POST" style="display: inline;">
                                    <input type="hidden" name="action" value="topic_feedback">
                                    <input type="hidden" name="topic_id" value="<?= $topic['id'] ?>">
                                    <input type="hidden" name="feedback_type" value="helpful">
                                    <button type="submit" class="feedback-btn helpful">👍 Helpful</button>
                                </form>
                                <form method="POST" style="display: inline;">
                                    <input type="hidden" name="action" value="topic_feedback">
                                    <input type="hidden" name="topic_id" value="<?= $topic['id'] ?>">
                                    <input type="hidden" name="feedback_type" value="not_helpful">
                                    <button type="submit" class="feedback-btn not_helpful">👎 Not Helpful</button>
                                </form>
                            </div>
                        </div>
                    <?php endforeach; ?>
                </div>
            <?php else: ?>
                <p class="text-muted">No topics generated yet. Click the button above to get started.</p>
            <?php endif; ?>
        </div>

        <div id="tab-insights" class="tab-content">
            <form method="POST" style="margin-bottom: 1.5rem;">
                <input type="hidden" name="action" value="analyze_dynamics">
                <input type="hidden" name="family_id" value="<?= htmlspecialchars($family_id) ?>">
                <button type="submit" class="btn" style="max-width: 300px;">Refresh Family Analysis</button>
            </form>

            <?php if ($dynamics): ?>
                <div class="dynamics-card">
                    <h3 style="margin-top: 0;">Family Dynamics</h3>

                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin: 1.5rem 0;">
                        <div style="text-align: center; padding: 1rem; background: #f0fdf4; border-radius: 0.5rem;">
                            <div style="font-size: 2rem; font-weight: bold; color: #166534;">
                                <?= round($dynamics['parent_engagement_score'] * 100) ?>%
                            </div>
                            <div style="font-size: 0.85rem; color: #666;">Parent Engagement</div>
                        </div>
                        <div style="text-align: center; padding: 1rem; background: #fef3c7; border-radius: 0.5rem;">
                            <div style="font-size: 2rem; font-weight: bold; color: #92400e;">
                                <?= round($dynamics['teen_engagement_score'] * 100) ?>%
                            </div>
                            <div style="font-size: 0.85rem; color: #666;">Teen Engagement</div>
                        </div>
                        <div style="text-align: center; padding: 1rem; background: #f3f4f6; border-radius: 0.5rem;">
                            <div style="font-size: 2rem; font-weight: bold; color: #374151;">
                                <?= round($dynamics['communication_gap'] * 100) ?>%
                            </div>
                            <div style="font-size: 0.85rem; color: #666;">Communication Gap</div>
                        </div>
                    </div>

                    <p><strong>Dynamics Pattern:</strong>
                        <?php
                        $pattern = $dynamics['dominant_role'] ?? 'balanced';
                        $patterns = [
                            'balanced' => '⚖️ Well Balanced',
                            'parent_led' => '👨‍👩‍👧 Parent-Led',
                            'teen_led' => '🧑‍🦱 Teen-Led'
                        ];
                        echo $patterns[$pattern] ?? $pattern;
                        ?>
                    </p>

                    <?php if (!empty($dynamics['suggested_focus_areas'])): ?>
                        <p><strong>Suggested Focus Areas:</strong></p>
                        <div style="margin-top: 0.5rem;">
                            <?php foreach (explode(';', $dynamics['suggested_focus_areas']) as $area): ?>
                                <span class="insight-tag"><?= htmlspecialchars(trim($area)) ?></span>
                            <?php endforeach; ?>
                        </div>
                    <?php endif; ?>
                </div>
            <?php else: ?>
                <div class="card">
                    <p>No dynamics data available yet. Click "Refresh Family Analysis" to generate insights.</p>
                </div>
            <?php endif; ?>

            <?php if (!empty($topic_effectiveness)): ?>
                <div class="dynamics-card" style="margin-top: 1rem;">
                    <h3>Topic Effectiveness</h3>
                    <p style="font-size: 0.9rem; color: #666;">Track which topics led to meaningful conversations</p>

                    <div style="overflow-x: auto;">
                        <table style="width: 100%; border-collapse: collapse; font-size: 0.9rem;">
                            <thead>
                                <tr style="border-bottom: 2px solid var(--border-color);">
                                    <th style="text-align: left; padding: 0.5rem;">Topic</th>
                                    <th style="text-align: center; padding: 0.5rem;">Discussed</th>
                                    <th style="text-align: center; padding: 0.5rem;">Helpful</th>
                                </tr>
                            </thead>
                            <tbody>
                                <?php foreach (array_slice($topic_effectiveness, 0, 5) as $t): ?>
                                    <tr style="border-bottom: 1px solid var(--border-color);">
                                        <td style="padding: 0.5rem;">
                                            <?= htmlspecialchars(mb_strimwidth($t['topic_text'], 0, 50, "...")) ?>
                                        </td>
                                        <td style="text-align: center; padding: 0.5rem;">
                                            <?= $t['discussed_count'] > 0 ? '✓' : '-' ?>
                                        </td>
                                        <td style="text-align: center; padding: 0.5rem; color: <?= $t['helpful_count'] > $t['not_helpful_count'] ? '#166534' : ($t['not_helpful_count'] > 0 ? '#dc2626' : '#666') ?>;">
                                            <?= $t['helpful_count'] ?> / <?= $t['not_helpful_count'] ?>
                                        </td>
                                    </tr>
                                <?php endforeach; ?>
                            </tbody>
                        </table>
                    </div>
                </div>
            <?php endif; ?>
        </div>

        <div id="tab-predictions" class="tab-content">
            <h3>Mood Predictions</h3>
            <p style="font-size: 0.9rem; color: #666; margin-bottom: 1.5rem;">
                AI-predicted emotional states based on recent check-in patterns
            </p>

            <?php if (!empty($predictions)): ?>
                <div style="display: grid; gap: 1rem;">
                    <?php foreach ($predictions as $pred): ?>
                        <div class="dynamics-card" style="display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                <strong><?= htmlspecialchars($pred['user_name']) ?></strong>
                                <span style="font-size: 0.8rem; color: #666;">(<?= htmlspecialchars($pred['role']) ?>)</span>
                            </div>
                            <div style="text-align: right;">
                                <span class="prediction-badge <?= htmlspecialchars($pred['trend'] ?? 'stable') ?>">
                                    <?= ucfirst($pred['predicted_mood'] ?? 'unknown') ?>
                                    (<?= round(($pred['confidence'] ?? 0) * 100) ?>%)
                                </span>
                                <div style="font-size: 0.75rem; color: #888; margin-top: 0.25rem;">
                                    Trend: <?= ucfirst($pred['trend'] ?? 'stable') ?>
                                </div>
                            </div>
                        </div>
                    <?php endforeach; ?>
                </div>
            <?php else: ?>
                <div class="card">
                    <p>No prediction data yet. Generate more check-ins to enable mood predictions.</p>
                </div>
            <?php endif; ?>
        </div>
    </div>

    <script>
        function showTab(tabName) {
            document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));

            document.getElementById('tab-' + tabName).classList.add('active');
            document.querySelector(`.tab-btn[onclick="showTab('${tabName}')"]`).classList.add('active');
        }

        document.getElementById('generate-form').addEventListener('submit', function(e) {
            e.preventDefault();

            const btn = document.getElementById('generate-btn');
            const spinner = document.getElementById('spinner');
            const text = btn.querySelector('span');

            btn.style.pointerEvents = 'none';
            btn.style.opacity = '0.8';
            text.innerText = 'Thinking with multiple AI models...';
            spinner.style.display = 'inline-block';

            let formData = new FormData(this);
            formData.append('ajax', '1');

            fetch('topics.php', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.error || data.empty_msg) {
                    this.submit();
                } else {
                    window.location.reload();
                }
            })
            .catch(err => {
                this.submit();
            });
        });
    </script>
</body>
</html>