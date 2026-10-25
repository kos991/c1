<?php require_once('../auth.php'); ?>
<?php if (isset($auth) && $auth) {?>
<?php
echo gwd_command('ui-NodeCUcheck');
?>
<?php }?>