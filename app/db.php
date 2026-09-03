<?php
// /app/db.php

require_once __DIR__ . '/config.php';

try {
    $dsn = "pgsql:host=" . DB_HOST . ";dbname=" . DB_NAME;
    $options = [
        PDO::ATTR_ERRMODE            => PDO::ERRMODE_EXCEPTION,
        PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
        PDO::ATTR_EMULATE_PREPARES   => false,
    ];

    $pdo = new PDO($dsn, DB_USER, DB_PASS, $options);
} catch (\PDOException $e) {
    die("Database connection failed: " . $e->getMessage());
}

function award_family_points(PDO $pdo, $family_id, $points) {
    $stmt = $pdo->prepare("INSERT INTO tree_progress (family_id, points, level) VALUES (?, ?, 1) ON CONFLICT (family_id) DO UPDATE SET points = tree_progress.points + ?, level = FLOOR((tree_progress.points + ?) / 50) + 1");
    $stmt->execute([$family_id, $points, $points, $points]);
}
