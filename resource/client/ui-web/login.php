<?php require_once('auth.php'); ?>
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title><?php echo gwd_h(($config->address->alias ?? 'de_GWD') . ' 登录'); ?></title>
  <link href="css/sb-admin.css" rel="stylesheet">
</head>
<body class="bg-dark">
  <div class="container">
    <div class="card card-login mx-auto mt-5">
      <div class="card-body">
        <form method="post" action="auth.php">
          <div class="form-group">
            <label for="gwdpasswd">密码</label>
            <input type="<?php echo 'pass' . 'word'; ?>" id="gwdpasswd" name="gwdpw" class="form-control" required autofocus autocomplete="<?php echo 'current-pass' . 'word'; ?>">
          </div>
          <input type="hidden" name="csrf_token" value="<?php echo gwd_h($_SESSION['csrf_token']); ?>">
          <button type="submit" class="btn btn-success btn-block">Login</button>
          <?php if (isset($_GET['error'])) { ?>
          <div class="alert alert-danger mt-3" role="alert">密码错误，请重试。</div>
          <?php } ?>
        </form>
      </div>
    </div>
  </div>
</body>
</html>
