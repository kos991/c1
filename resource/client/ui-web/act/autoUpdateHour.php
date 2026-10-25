<?php require_once('../auth.php'); ?>
<?php if (isset($auth) && $auth) {?>
<?php
$autoUpdateHourINDEX = gwd_string('autoUpdateHourINDEX');

$data = json_decode(file_get_contents('/opt/de_GWD/0conf'), true);
$data['address']['autoUpdateHour'] = $autoUpdateHourINDEX;
$newJsonString = json_encode($data, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
file_put_contents('/opt/de_GWD/0conf', $newJsonString);

gwd_command('ui-autoUpdateHour', [$autoUpdateHourINDEX], true);
?>
<?php }?>
