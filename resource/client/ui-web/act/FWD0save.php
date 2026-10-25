<?php require_once('../auth.php'); ?>
<?php require_once __DIR__ . '/helpers.php'; ?>
<?php if (isset($auth) && $auth) {?>
<?php
$FWD0port = gwd_integer('FWD0port', 1, 65535);
$FWD0uuidList = gwd_rows('FWD0uuidList', ['FWD0uuid', 'FWD0mark']);

$data = json_decode(file_get_contents('/opt/de_GWD/0conf'), true);
$data['FORWARD']['FWD0'] = array();
$data['FORWARD']['FWD0']['status'] = "on";
$data['FORWARD']['FWD0']['port'] = $FWD0port;
$data['FORWARD']['FWD0']['uuid'] = $FWD0uuidList;
$newJsonString = json_encode($data, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
file_put_contents('/opt/de_GWD/0conf', $newJsonString);

gwd_command('ui-FWD0save', [], true);
?>
<?php }?>
