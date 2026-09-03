<?php
// /public/index.php
require_once __DIR__ . '/../app/db.php';
require_once __DIR__ . '/../app/auth.php';

if (is_logged_in()) {
    header('Location: dashboard.php');
    exit;
}
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>EmoLink - Welcome</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500;9..144,600;9..144,700&family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="assets/style.css">
</head>
<body>
    <div class="auth-container">
        <div class="card text-center">
            <h1>Welcome to EmoLink</h1>
            <p class="mb-4 text-muted">An AI-powered family emotional-connection platform.</p>
            <a href="login.php" class="btn mb-4">Log In</a>
            <a href="register.php" class="btn btn-outline">Register</a>
        </div>
    </div>
</body>
</html>
