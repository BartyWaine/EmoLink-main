<?php
session_start();

$db_host = getenv('DB_HOST') ?: 'localhost';
$db_name = getenv('DB_NAME') ?: 'railway';
$db_user = getenv('DB_USER') ?: 'root';
$db_pass = getenv('DB_PASS') ?: '';

define('DB_HOST', $db_host);
define('DB_NAME', $db_name);
define('DB_USER', $db_user);
define('DB_PASS', $db_pass);

$ai_url = getenv('AI_SERVICE_URL') ?: 'https://emolink-ai.vercel.app';
define('AI_SERVICE_URL', $ai_url);
