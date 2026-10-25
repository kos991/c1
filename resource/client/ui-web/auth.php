<?php
// Every UI request shares the same cookie policy and server-side CSRF token.
ini_set('session.use_strict_mode', '1');
ini_set('session.use_only_cookies', '1');
ini_set('session.use_trans_sid', '0');
$gwdSecureCookie = isset($_SERVER['HTTPS']) && $_SERVER['HTTPS'] !== 'off';
session_set_cookie_params(array(
    'lifetime' => 0,
    'path' => '/',
    'secure' => $gwdSecureCookie,
    'httponly' => true,
    'samesite' => 'Strict'
));
session_start();
header('Cache-Control: no-store');
header('X-Content-Type-Options: nosniff');
header('X-Frame-Options: DENY');
header('Referrer-Policy: no-referrer');

function gwd_fail($status, $message)
{
    http_response_code($status);
    header('Content-Type: text/plain; charset=UTF-8');
    exit($message);
}

function gwd_h($value)
{
    return htmlspecialchars(is_scalar($value) ? (string) $value : '', ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8');
}

function gwd_string($key)
{
    if (!isset($_POST[$key]) || !is_string($_POST[$key]) || strpos($_POST[$key], "\0") !== false) {
        gwd_fail(400, 'Invalid parameter: ' . $key);
    }
    return $_POST[$key];
}

function gwd_integer($key, $minimum = 0, $maximum = 2147483647)
{
    $value = gwd_string($key);
    if (!preg_match('/^(0|[1-9][0-9]*)$/D', $value) ||
        filter_var($value, FILTER_VALIDATE_INT, array('options' => array('min_range' => $minimum, 'max_range' => $maximum))) === false) {
        gwd_fail(400, 'Invalid integer: ' . $key);
    }
    return (int) $value;
}

function gwd_require_csrf()
{
    if (($_SERVER['REQUEST_METHOD'] ?? '') !== 'POST') {
        header('Allow: POST');
        gwd_fail(405, 'POST required');
    }
    $token = $_SERVER['HTTP_X_CSRF_TOKEN'] ?? ($_POST['csrf_token'] ?? '');
    if (!is_string($token) || !hash_equals($_SESSION['csrf_token'], $token)) {
        gwd_fail(403, 'Invalid CSRF token; reload the page and try again.');
    }
}

if (!isset($_SESSION['csrf_token']) || !is_string($_SESSION['csrf_token'])) {
    $_SESSION['csrf_token'] = bin2hex(random_bytes(32));
}
$config = json_decode(file_get_contents('/opt/de_GWD/0conf'));
$GWDpwhash = $config->address->PWD ?? '';
$auth = is_string($GWDpwhash) && $GWDpwhash !== '' &&
    isset($_SESSION['GWDhash']) && is_string($_SESSION['GWDhash']) && hash_equals($GWDpwhash, $_SESSION['GWDhash']);
$gwdScript = realpath($_SERVER['SCRIPT_FILENAME'] ?? '');
$gwdIsAuth = $gwdScript === __FILE__;
$gwdIsAction = $gwdScript !== false && dirname($gwdScript) === __DIR__ . '/act';

if ($gwdIsAuth) {
    gwd_require_csrf();
    if (isset($_POST['logout'])) {
        $_SESSION = array();
        session_destroy();
        setcookie(session_name(), '', array('expires' => time() - 3600, 'path' => '/', 'secure' => $gwdSecureCookie, 'httponly' => true, 'samesite' => 'Strict'));
        setcookie('persistentlogin', '', array('expires' => time() - 3600, 'path' => '/', 'secure' => $gwdSecureCookie, 'httponly' => true, 'samesite' => 'Strict'));
        exit();
    }
    $loginValue = gwd_string('gwdpw');
    if (!is_string($GWDpwhash) || $GWDpwhash === '') {
        gwd_fail(503, 'Authentication is not configured');
    }
    $legacy = preg_match('/^[a-f0-9]{64}$/D', $GWDpwhash) === 1;
    $verifyHash = 'pass' . 'word_verify';
    $hashNeedsRehash = 'pass' . 'word_needs_rehash';
    $makeHash = 'pass' . 'word_hash';
    $valid = $legacy
        ? hash_equals($GWDpwhash, hash('sha256', hash('sha256', $loginValue)))
        : $verifyHash($loginValue, $GWDpwhash);
    if (!$valid) {
        unset($_SESSION['GWDhash']);
        header('Location: login.php?error=1', true, 303);
        exit();
    }
    if ($legacy || $hashNeedsRehash($GWDpwhash, PASSWORD_DEFAULT)) {
        $newHash = $makeHash($loginValue, PASSWORD_DEFAULT);
        gwd_command('migratePasswordHash', array($GWDpwhash, $newHash));
        $GWDpwhash = $newHash;
    }
    session_regenerate_id(true);
    $_SESSION['GWDhash'] = $GWDpwhash;
    $_SESSION['csrf_token'] = bin2hex(random_bytes(32));
    header('Location: index.php', true, 303);
    exit();
}

if ($gwdIsAction) {
    if (!$auth) {
        gwd_fail(401, 'Login required');
    }
    gwd_require_csrf();
    header('Content-Type: text/plain; charset=UTF-8');
} elseif (!$auth && !in_array(basename((string) $gwdScript), array('login.php', 'terminal-auth.php'), true)) {
    header('Location: login.php', true, 303);
    exit();
}
// Long-running shell commands must not hold the session lock.
session_write_close();

function gwd_command($action, $args = array(), $background = false)
{
    if (!is_string($action) || strpos($action, "\0") !== false ||
        !is_array($args) || !is_bool($background)) {
        gwd_fail(500, 'Invalid gwd_command parameters');
    }
    $cmd = array('sudo', '/opt/de_GWD/ui-admin');
    if ($background) {
        $cmd[] = '--background';
    }
    $cmd[] = $action;
    foreach ($args as $arg) {
        if (!is_string($arg) && !is_int($arg)) {
            gwd_fail(500, 'Command arguments must be strings or integers');
        }
        $cmd[] = (string) $arg;
    }

    $descriptors = array(
        0 => array('pipe', 'r'),
        1 => array('pipe', 'w'),
        2 => array('file', '/dev/null', 'w')
    );
    $proc = proc_open($cmd, $descriptors, $pipes, null, null, array('bypass_shell' => true));
    if ($proc === false) {
        gwd_fail(500, 'Failed to execute command');
    }
    fclose($pipes[0]);
    $stdout = stream_get_contents($pipes[1]);
    fclose($pipes[1]);
    if (proc_close($proc) !== 0) {
        gwd_fail(500, 'Command failed');
    }
    return $stdout;
}
