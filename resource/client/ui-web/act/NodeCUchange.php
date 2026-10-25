<?php require_once('../auth.php'); ?>
<?php if (isset($auth) && $auth) {?>
<?php
$nodeCUnum = gwd_integer('nodeCUnum', 0, 2147483647);
gwd_command('ui-NodeCUchange', [$nodeCUnum]);
?>
<?php }?>