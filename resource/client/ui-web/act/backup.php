<?php require_once('../auth.php'); ?>
<?php if (isset($auth) && $auth) {?>
<?php
gwd_command('backup', ['de_GWD']);
?>
<?php }?>