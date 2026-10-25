<?php
/**
 * Terminal authentication endpoint for nginx internal auth_request
 * Used by nginx `auth_request /terminal-auth.php` for ttyd gateway
 *
 * Returns:
 * - 204 No Content: authenticated, session valid, Origin matches
 * - 401 Unauthorized: not authenticated or session invalid
 * - 403 Forbidden: Origin mismatch (same-site policy)
 */
require_once('auth.php');

header('Cache-Control: no-store');

if (!$auth) {
    http_response_code(401);
    exit();
}

// WebSocket requests have an Origin; it must match this exact browser origin.
$origin = $_SERVER['HTTP_ORIGIN'] ?? '';
if ($origin !== '') {
    $parsed = parse_url($origin);
    $originHost = is_array($parsed) && isset($parsed['host']) ? strtolower($parsed['host']) : '';
    $originScheme = is_array($parsed) ? strtolower($parsed['scheme'] ?? '') : '';
    $originPort = is_array($parsed) ? ($parsed['port'] ?? ($originScheme === 'https' ? 443 : 80)) : 0;
    $host = strtolower($_SERVER['HTTP_HOST'] ?? '');
    $requestScheme = (!empty($_SERVER['HTTPS']) && $_SERVER['HTTPS'] !== 'off') ? 'https' : 'http';
    $expected = parse_url($requestScheme . '://' . $host);
    $expectedHost = strtolower($expected['host'] ?? '');
    $expectedPort = $expected['port'] ?? ($requestScheme === 'https' ? 443 : 80);
    if (!in_array($originScheme, array('http', 'https'), true) ||
        $originScheme !== $requestScheme ||
        $originHost !== $expectedHost || $originPort !== $expectedPort ||
        isset($parsed['user']) || isset($parsed['pass']) ||
        isset($parsed['path']) || isset($parsed['query']) || isset($parsed['fragment'])) {
        http_response_code(403);
        exit();
    }
}

// A direct same-site page request has no Origin header.
http_response_code(204);
exit();
