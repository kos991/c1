<?php
require_once('../auth.php');
$speedT = gwd_integer('speedT', 0, 2147483647);
echo gwd_command('ui-speedT', [$speedT]);
?>
