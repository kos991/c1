<?php require_once('../auth.php'); ?>
<?php require_once __DIR__ . '/helpers.php'; ?>
<?php if (isset($auth) && $auth) {?>
<?php
$conf = json_decode(file_get_contents('/opt/de_GWD/0conf'), true);
$nodeList = gwd_rows('nodeList', ['domain', 'tls', 'name', 'uuid', 'path']);

$conf['v2node'] = $nodeList;
$newJsonString = json_encode($conf, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
file_put_contents('/opt/de_GWD/0conf', $newJsonString);

gwd_command('ui-NodeSave', [], true);
?>
<?php }?>