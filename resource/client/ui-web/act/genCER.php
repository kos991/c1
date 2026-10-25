<?php require_once('../auth.php'); ?>
<?php if (isset($auth) && $auth) {?>
<?php
$conf = json_decode(file_get_contents('/opt/de_GWD/0conf'), true);
$CFdomain = gwd_string('CFdomain');
$CFapikey = gwd_string('CFapikey');
$CFemail = gwd_string('CFemail');

$conf['FORWARD']['domain'] = $CFdomain;
$conf['FORWARD']['APIkey'] = $CFapikey;
$conf['FORWARD']['Email'] = $CFemail;
$newJsonString = json_encode($conf, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
file_put_contents('/opt/de_GWD/0conf', $newJsonString);

gwd_command('install', ['CER'], true);
?>
<?php }?>