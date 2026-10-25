<?php require_once('../auth.php'); ?>
<?php if (isset($auth) && $auth) {?>
<?php
$nodeDTnum = gwd_integer('nodeDTnum', 0, 2147483647);
gwd_command('ui-NodeDTchange', [$nodeDTnum]);
?>
<?php }?>