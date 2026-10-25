<?php
require_once('../auth.php');
$pingTCP = gwd_integer('pingTCP', 0, 2147483647);
echo gwd_command('ui-pingTCP', [$pingTCP]);
die();
?>
