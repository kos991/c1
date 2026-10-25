<?php
require_once('../auth.php');

if (!$auth) {
    gwd_fail(401, 'Login required');
}

gwd_require_csrf();

if (gwd_string('kind') !== 'de_GWD') gwd_fail(400, 'Invalid backup kind');
$filename = 'de_GWD_bak';

$filepath = '/var/lib/de_GWD/restore/' . $filename;

// Open once, then verify the same file descriptor before streaming.
if (is_link($filepath)) gwd_fail(404, 'Backup not found');
$handle = @fopen($filepath, 'rb');
if ($handle === false) gwd_fail(404, 'Backup not found');
$stat = fstat($handle);
$pathStat = lstat($filepath);
if ($stat === false || $pathStat === false || ($stat['mode'] & 0170000) !== 0100000 ||
    ($pathStat['mode'] & 0170000) !== 0100000 || $stat['dev'] !== $pathStat['dev'] ||
    $stat['ino'] !== $pathStat['ino'] || $stat['uid'] !== 0 || $stat['nlink'] !== 1) {
    fclose($handle);
    gwd_fail(404, 'Backup not found');
}

header('Content-Type: application/octet-stream');
header('Content-Disposition: attachment; filename="' . $filename . '"');
header('Content-Length: ' . $stat['size']);
header('Cache-Control: no-cache, no-store, must-revalidate');
fpassthru($handle);
fclose($handle);
exit();
