<?php
require_once('../auth.php');
// The installer places the installed release tag outside the web tree.
$lines = @file('/var/lib/de_GWD/version.php');
$current = is_array($lines) ? trim($lines[0] ?? '') : '';
if (!preg_match('/^v\d+\.\d+\.\d+$/D', $current)) gwd_fail(500, 'Invalid installed version');
$context = stream_context_create(['http' => ['timeout' => 3, 'follow_location' => 0, 'header' => "Cache-Control: no-cache\r\nPragma: no-cache\r\n"]]);
$remote = @file_get_contents('https://raw.githubusercontent.com/kos991/c1/main/version.php', false, $context, 0, 128);
$published = is_string($remote) ? trim(strtok($remote, "\r\n")) : '';
if (!preg_match('/^v\d+\.\d+\.\d+(?:\+C1)?$/D', $published)) $published = '';
$version = $published !== '' ? preg_replace('/\+C1$/D', '', $published) : '';
header('Content-Type: application/json; charset=UTF-8');
echo json_encode([
    'installed' => $current,
    'published' => $version,
    'updateAvailable' => $version !== '' && version_compare(substr($version, 1), substr($current, 1), '>'),
    'legacyPublished' => $published !== '' && str_ends_with($published, '+C1'),
]);
