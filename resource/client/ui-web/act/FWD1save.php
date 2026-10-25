<?php require_once('../auth.php'); ?>
<?php require_once __DIR__ . '/helpers.php'; ?>
<?php if (isset($auth) && $auth) {?>
<?php
$FWD1port = gwd_integer('FWD1port', 1, 65535);
$FWD1uuidList = gwd_rows('FWD1uuidList', ['FWD1uuid', 'FWD1mark']);
$FWD1upstream = gwd_string('FWD1upstream');

$data = json_decode(file_get_contents('/opt/de_GWD/0conf'), true);
$data['FORWARD']['FWD1'] = array();
$data['FORWARD']['FWD1']['status'] = "on";
$data['FORWARD']['FWD1']['port'] = $FWD1port;
$data['FORWARD']['FWD1']['uuid'] = $FWD1uuidList;
$data['FORWARD']['FWD1']['upstream'] = $FWD1upstream;
$newJsonString = json_encode($data, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
file_put_contents('/opt/de_GWD/0conf', $newJsonString);

gwd_command('ui-FWD1save', [], true);
?>
<?php }?>
