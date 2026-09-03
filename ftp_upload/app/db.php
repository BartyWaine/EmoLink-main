<?php
// /app/db.php

require_once __DIR__ . '/config.php';

try {
    $dsn = "mysql:host=" . DB_HOST . ";dbname=" . DB_NAME . ";charset=utf8mb4";
    $options = [
        PDO::ATTR_ERRMODE            => PDO::ERRMODE_EXCEPTION, // Throw exceptions on errors
        PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,       // Fetch associative arrays
        PDO::ATTR_EMULATE_PREPARES   => false,                  // Use real prepared statements
    ];
    
    $pdo = new PDO($dsn, DB_USER, DB_PASS, $options);
} catch (\PDOException $e) {
    // In a production environment, we'd log this instead of outputting directly
    die("Database connection failed: " . $e->getMessage());
}

// Helper to award points and calculate level (50 points = 1 level)
function award_family_points(PDO $pdo, $family_id, $points) {
    // Ensure the row exists first
    $stmt = $pdo->prepare("INSERT IGNORE INTO tree_progress (family_id, points, level) VALUES (?, 0, 1)");
    $stmt->execute([$family_id]);
    
    // Increment points and calculate new level safely
    $stmt = $pdo->prepare("
        UPDATE tree_progress 
        SET points = points + ?, 
            level = FLOOR((points + ?) / 50) + 1 
        WHERE family_id = ?
    ");
    $stmt->execute([$points, $points, $family_id]);
}
