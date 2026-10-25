<?php require_once('../auth.php'); ?>
<?php if (isset($auth) && $auth) {?>
<?php
$nodeSMshowYoutube = gwd_integer('nodeSMshowYoutube', 0, 2147483647);
$nodeSMshowNetflix = gwd_integer('nodeSMshowNetflix', 0, 2147483647);
$nodeSMshowHDH = gwd_integer('nodeSMshowHDH', 0, 2147483647);
$nodeSMshowTVB = gwd_integer('nodeSMshowTVB', 0, 2147483647);
$nodeSMshowBahamut = gwd_integer('nodeSMshowBahamut', 0, 2147483647);
$nodeSMshowOpenai = gwd_integer('nodeSMshowOpenai', 0, 2147483647);
$nodeSMshowGpt = gwd_integer('nodeSMshowGpt', 0, 2147483647);
$nodeSMshowClaude = gwd_integer('nodeSMshowClaude', 0, 2147483647);
$nodeSMshowApple = gwd_integer('nodeSMshowApple', 0, 2147483647);
$nodeSMshowSteam = gwd_integer('nodeSMshowSteam', 0, 2147483647);
gwd_command('ui-NodeSMrules', [$nodeSMshowYoutube, $nodeSMshowNetflix, $nodeSMshowHDH, $nodeSMshowTVB, $nodeSMshowBahamut, $nodeSMshowOpenai, $nodeSMshowGpt, $nodeSMshowClaude, $nodeSMshowApple, $nodeSMshowSteam]);
?>
<?php }?>
