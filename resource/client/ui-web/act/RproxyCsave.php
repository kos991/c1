<?php require_once('../auth.php'); ?>
<?php require_once __DIR__ . '/helpers.php'; ?>
<?php if (isset($auth) && $auth) {?>
<?php
$RproxyCtunnelAddress = gwd_string('RproxyCtunnelAddress');
$RproxyCtunnelUUID = gwd_string('RproxyCtunnelUUID');
$RproxyCoutStatus = gwd_string('RproxyCoutStatus');
$RproxyCmappingStatus = gwd_string('RproxyCmappingStatus');
$RproxyC1List = gwd_rows('RproxyC1List', ['extPort', 'extProtocol', 'intIP', 'intPort']);

$data = json_decode(file_get_contents('/opt/de_GWD/0conf'), true);
$data['FORWARD']['Rproxy']['client'] = array();
$data['FORWARD']['Rproxy']['client']['status'] = "on";
if ($RproxyCoutStatus === block) $data['FORWARD']['Rproxy']['client']['outStatus'] = "on";
if ($RproxyCmappingStatus === block) $data['FORWARD']['Rproxy']['client']['mappingStatus'] = "on";
$data['FORWARD']['Rproxy']['client']['tunnel']['address'] = $RproxyCtunnelAddress;
$data['FORWARD']['Rproxy']['client']['tunnel']['uuid'] = $RproxyCtunnelUUID;
$data['FORWARD']['Rproxy']['client']['mapping'] = $RproxyC1List;
$newJsonString = json_encode($data, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
file_put_contents('/opt/de_GWD/0conf', $newJsonString);

gwd_command('ui-RproxyCsave', [], true);
?>
<?php }?>
