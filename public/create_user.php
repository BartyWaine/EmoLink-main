<?php
// Quick user registration script
require_once __DIR__ . '/../app/db.php';

// Get credentials from command line or use defaults
$name = $argv[1] ?? 'Test User';
$email = $argv[2] ?? 'test@example.com';
$password = $argv[3] ?? 'password123';
$role = $argv[4] ?? 'parent'; // 'parent' or 'teen'

// Hash password
$password_hash = password_hash($password, PASSWORD_DEFAULT);

try {
    // Insert user
    $stmt = $pdo->prepare("INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)");
    $stmt->execute([$name, $email, $password_hash]);
    $user_id = $pdo->lastInsertId();

    // Create a family for this user
    $family_name = $name . "'s Family";
    $invite_code = strtoupper(substr(md5(uniqid()), 0, 6));

    $stmt = $pdo->prepare("INSERT INTO families (family_name, invite_code) VALUES (?, ?)");
    $stmt->execute([$family_name, $invite_code]);
    $family_id = $pdo->lastInsertId();

    // Add user to family
    $stmt = $pdo->prepare("INSERT INTO family_members (family_id, user_id, role) VALUES (?, ?, ?)");
    $stmt->execute([$family_id, $user_id, $role]);

    // Initialize tree progress
    $stmt = $pdo->prepare("INSERT INTO tree_progress (family_id, points, level) VALUES (?, 0, 1)");
    $stmt->execute([$family_id]);

    echo "========================================\n";
    echo "Account Created Successfully!\n";
    echo "========================================\n";
    echo "Name: $name\n";
    echo "Email: $email\n";
    echo "Password: $password\n";
    echo "Role: $role\n";
    echo "Family: $family_name\n";
    echo "Invite Code: $invite_code\n";
    echo "========================================\n";
    echo "\nYou can now login at:\n";
    echo "http://localhost:8080/emolink/public/login.php\n";

} catch (PDOException $e) {
    echo "Error: " . $e->getMessage() . "\n";
}
