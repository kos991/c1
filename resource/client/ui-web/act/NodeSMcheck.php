<?php require_once('../auth.php'); ?>
<?php if (isset($auth) && $auth) {?>
<?php
print gwd_command('ui-NodeSMcheck');
?>
<?php }?>