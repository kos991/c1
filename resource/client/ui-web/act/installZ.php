<?php require_once('../auth.php'); ?>
<?php if (isset($auth) && $auth) {?>
<?php
gwd_command('ui-installZ', [], true);
?>
<?php }?>
