<?php require_once('../auth.php'); ?>
<?php if (isset($auth) && $auth) {?>
<?php
$nodenum = gwd_integer('nodenum', 0, 2147483647);
gwd_command('ui-NodeChange', [$nodenum], true);
?>
<?php }?>