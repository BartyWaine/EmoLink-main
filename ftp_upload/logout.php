<?php
// /public/logout.php
require_once __DIR__ . '/../app/auth.php';

session_start();
session_unset();
session_destroy();

header('Location: login.php');
exit;
