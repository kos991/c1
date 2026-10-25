<?php require_once('../auth.php'); ?>
<?php if (isset($auth) && $auth) {?>
<?php
$localip = gwd_string('localip');
$upstreamip = gwd_string('upstreamip');

$data = json_decode(file_get_contents('/opt/de_GWD/0conf'), true);
$data['address']['localIP'] = $localip;
$data['address']['upstreamIP'] = $upstreamip;
$newJsonString = json_encode($data, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
file_put_contents('/opt/de_GWD/0conf', $newJsonString);

gwd_command('ui-reboot', [], true);
?>
<?php }?>