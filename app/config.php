<?php
// Start the session for user authentication
session_start();

// Database credentials - Render Postgres
$db_url = getenv('DATABASE_URL');
if ($db_url) {
    // Parse postgres://user:pass@host:port/dbname
    $parsed = parse_url($db_url);
    parse_str($parsed['query'], $query);
    $db_parts = explode('/', $parsed['path']);
    $db_name = end($db_parts);

    define('DB_HOST', $parsed['host']);
    define('DB_NAME', $db_name);
    define('DB_USER', $parsed['user']);
    define('DB_PASS', $parsed['pass']);
} else {
    // Fallback for local development
    define('DB_HOST', getenv('DB_HOST') ?: 'localhost');
    define('DB_NAME', getenv('DB_NAME') ?: 'emolink');
    define('DB_USER', getenv('DB_USER') ?: 'root');
    define('DB_PASS', getenv('DB_PASS') ?: '');
}

// AI Service URL
define('AI_SERVICE_URL', getenv('AI_SERVICE_URL') ?: 'https://emolink-ai.vercel.app');
