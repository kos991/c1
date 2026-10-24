v2.0.0+C1
-
<?php
$str= file_get_contents('https://raw.githubusercontent.com/kos991/c1/main/version.php');
$array=explode('-', $str);
echo $array[0];
?>
