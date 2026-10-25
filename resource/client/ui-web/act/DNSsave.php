<?php require_once('../auth.php'); ?>
<?php if (isset($auth) && $auth) {?>
<?php
$conf = json_decode(file_get_contents('/opt/de_GWD/0conf'), true);
if (!is_array($conf) || !isset($conf['dns']) || !is_array($conf['dns'])) {
    gwd_fail(500, 'DNS configuration unavailable');
}

function gwd_dns_hostname($host)
{
    if (strlen($host) > 253 || $host === '') {
        return false;
    }
    foreach (explode('.', $host) as $label) {
        if (!preg_match('/^[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?$/D', $label)) {
            return false;
        }
    }
    return true;
}

function gwd_dns_port($port)
{
    return preg_match('/^[0-9]{1,5}$/D', $port) && (int) $port >= 1 && (int) $port <= 65535;
}

$dog = trim(gwd_string('DoGc'));
if ($dog !== '') {
    $parts = explode(':', $dog);
    if (count($parts) !== 2 || !gwd_dns_hostname($parts[0]) || !gwd_dns_port($parts[1])) {
        gwd_fail(400, 'Invalid DNS-over-gRPC endpoint');
    }
}

$doh = array();
foreach (array('DoH1', 'DoH2') as $key) {
    $endpoint = trim(gwd_string($key));
    if ($endpoint !== '') {
        $parts = explode('/', $endpoint, 2);
        $authority = explode(':', $parts[0]);
        if (count($authority) > 2 || !gwd_dns_hostname($authority[0]) ||
            (count($authority) === 2 && !gwd_dns_port($authority[1])) ||
            (count($parts) === 2 && ($parts[1] === '' || !preg_match('~^[a-zA-Z0-9/_?&=%.-]+$~D', $parts[1])))) {
            gwd_fail(400, 'Invalid DNS-over-HTTPS endpoint: ' . $key);
        }
    }
    $doh[] = $endpoint;
}

$chinaServers = preg_split('/\s+/', trim(gwd_string('dnsChina')), -1, PREG_SPLIT_NO_EMPTY);
foreach ($chinaServers as $server) {
    $parts = explode(':', $server);
    if (count($parts) > 2 || !filter_var($parts[0], FILTER_VALIDATE_IP, FILTER_FLAG_IPV4) ||
        (count($parts) === 2 && !gwd_dns_port($parts[1]))) {
        gwd_fail(400, 'Invalid domestic DNS server');
    }
}

$hosts = array();
$lines = preg_split('/\r\n|\n|\r/', gwd_string('hostsCustomize'));
foreach ($lines as $line) {
    $line = trim($line);
    if ($line === '') {
        continue;
    }
    $fields = preg_split('/\s+/', $line);
    if (count($fields) !== 2 || !filter_var($fields[0], FILTER_VALIDATE_IP, FILTER_FLAG_IPV4)) {
        gwd_fail(400, 'Invalid hosts entry');
    }
    $host = $fields[1];
    $domain = strncmp($host, '*.', 2) === 0 ? substr($host, 2) : $host;
    if (!gwd_dns_hostname($domain)) {
        gwd_fail(400, 'Invalid hosts domain');
    }
    $hosts[$host] = $fields[0];
}

$conf['dns']['dog'] = $dog;
$conf['dns']['doh'] = $doh;
$conf['dns']['china'] = implode(' ', $chinaServers);
$conf['dns']['hosts'] = $hosts;
$json = json_encode($conf, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
if ($json === false || file_put_contents('/opt/de_GWD/0conf', $json, LOCK_EX) === false) {
    gwd_fail(500, 'Failed to save DNS settings');
}
gwd_command('ui_4h', array(), true);
?>
<?php }?>