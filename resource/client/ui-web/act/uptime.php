<?php
require_once('../auth.php');
$seconds = @file_get_contents('/proc/uptime');
if ($seconds === false || !is_numeric(strtok($seconds, ' '))) {
    gwd_fail(500, 'Uptime unavailable');
}
$minutes = (int) floor((float) strtok($seconds, ' ') / 60);
$days = intdiv($minutes, 1440);
$hours = intdiv($minutes % 1440, 60);
$minutes %= 60;
echo ($days ? $days . '天' : '') . ($hours ? $hours . '小时' : '') . $minutes . '分钟';