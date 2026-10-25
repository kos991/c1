<?php require_once('../auth.php'); ?>
<?php if (isset($auth) && $auth) {?>
<?php
$switchNodeCU = gwd_string('switchNodeCU');
if ($switchNodeCU == "NodeCUshow"){
    gwd_command('ui-NodeCU', [], true);
}
elseif ($switchNodeCU == "NodeCUhide"){
    gwd_command('ui-NodeCUhide', [], true);
}

echo gwd_command('ui-NodeCUcheck');
?>
<?php }?>