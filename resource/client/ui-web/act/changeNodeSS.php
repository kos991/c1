<?php require_once('../auth.php'); ?>
<?php if (isset($auth) && $auth) {?>
<?php
$ssAddress = gwd_string('ssAddress');
$ssPort = gwd_string('ssPort');
$ssMethod = gwd_string('ssMethod');
$ssSecure = gwd_string('ssSecure');

$data = json_decode(file_get_contents('/opt/de_GWD/0conf'), true);
$data['v2nodeDIV']['ss'] = array();
$data['v2nodeDIV']['ss']['ssAddress'] = $ssAddress;
$data['v2nodeDIV']['ss']['ssPort'] = $ssPort;
$data['v2nodeDIV']['ss']['ssMethod'] = $ssMethod;
$data['v2nodeDIV']['ss']['ssSecure'] = $ssSecure;
$newJsonString = json_encode($data, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
file_put_contents('/opt/de_GWD/0conf', $newJsonString);

gwd_command('ui-changeNodeSS', [], true);
?>
<?php }?>