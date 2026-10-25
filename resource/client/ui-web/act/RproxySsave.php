<?php require_once('../auth.php'); ?>
<?php require_once __DIR__ . '/helpers.php'; ?>
<?php if (isset($auth) && $auth) {?>
<?php
$RproxyStunnelPort = gwd_integer('RproxyStunnelPort', 1, 65535);
$RproxyStunnelUUID = gwd_string('RproxyStunnelUUID');
$RproxySinStatus = gwd_string('RproxySinStatus');
$RproxyS0uuidList = gwd_rows('RproxyS0uuidList', ['RproxyS0uuid', 'RproxyS0mark']);
$RproxySmappingStatus = gwd_string('RproxySmappingStatus');
$RproxyS1List = gwd_rows('RproxyS1List', ['port', 'protocol']);

$data = json_decode(file_get_contents('/opt/de_GWD/0conf'), true);
$data['FORWARD']['Rproxy']['server'] = array();
$data['FORWARD']['Rproxy']['server']['status'] = "on";
if ($RproxySinStatus === block) $data['FORWARD']['Rproxy']['server']['inStatus'] = "on";
if ($RproxySmappingStatus === block) $data['FORWARD']['Rproxy']['server']['mappingStatus'] = "on";
$data['FORWARD']['Rproxy']['server']['tunnel']['port'] = $RproxyStunnelPort;
$data['FORWARD']['Rproxy']['server']['tunnel']['uuid'] = $RproxyStunnelUUID;
$data['FORWARD']['Rproxy']['server']['inUUID'] = $RproxyS0uuidList;
$data['FORWARD']['Rproxy']['server']['mapping'] = $RproxyS1List;
$newJsonString = json_encode($data, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
file_put_contents('/opt/de_GWD/0conf', $newJsonString);

gwd_command('ui-RproxySsave', [], true);
?>
<?php }?>
