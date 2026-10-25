<?php require_once('../auth.php'); ?>
<?php require_once __DIR__ . '/helpers.php'; ?>
<?php if (isset($auth) && $auth) { ?>
<?php
$id = gwd_restore_upload('de_GWD_bak');
gwd_command('ui-restore', [$id], true);
?>
<?php } ?>
