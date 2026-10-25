<?php require_once('../auth.php'); ?>
<?php if (isset($auth) && $auth) {?>
<?php
$switchNodeDT = gwd_string('switchNodeDT');
if ($switchNodeDT == "NodeDTshow"){
    gwd_command('ui-NodeDT', [], true);
}
elseif ($switchNodeDT == "NodeDThide"){
    gwd_command('ui-NodeDThide', [], true);
}

echo gwd_command('ui-NodeDTcheck');
?>
<?php }?>