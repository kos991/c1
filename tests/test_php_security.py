"""Run on Debian with python3 -m unittest discover -s tests."""
import pathlib
import re
import shutil
import subprocess
import tempfile
import unittest

if shutil.which('dpkg') is None:
    raise unittest.SkipTest('PHP package test requires Debian dpkg; run it on Debian')


INSTALLER = pathlib.Path(__file__).resolve().parents[1] / "client"
FUNCTION = re.search(
    r"^installSecurePHP\(\)\{\n.*?^\}",
    INSTALLER.read_text(encoding="utf-8"),
    re.MULTILINE | re.DOTALL,
).group(0)


class PHPSecurityUpgrade(unittest.TestCase):
    def run_scenario(self, scenario):
        with tempfile.TemporaryDirectory() as directory:
            script = r'''
scenario=$1
state=$2
export LC_ALL=C
apt-get(){
    printf '%s\n' "$*" >>"$state/apt"
    [[ $scenario = apt-failure ]] && return 1
    if [[ $1 = install && $scenario != stale-candidate ]]; then
        touch "$state/upgraded"
    fi
    return 0
}
systemctl(){ printf '%s\n' "$*" >>"$state/service"; }
dpkg-query(){
    local package=${@: -1}
    local version='1:7.4.33-30+0~20260703.1+debian13~1'
    [[ $scenario = patched || -f $state/upgraded ]] && version='1:7.4.33-31+0~20261021.121+debian13~1'
    if [[ $package = 'php7.4*' ]]; then
        printf 'php7.4-readline installed %s php7.4\n' "$version"
        printf 'php7.4-imagick installed 3.8.0-1 php-imagick\n'
    elif [[ $scenario = missing && ! -f $state/upgraded && $package = php7.4-fpm ]]; then
        return 1
    else
        printf 'installed %s\n' "$version"
    fi
}
'''
            result = subprocess.run(
                ["bash", "-s", "--", scenario, directory],
                input=script + FUNCTION + "\ninstallSecurePHP\n",
                text=True,
                capture_output=True,
                check=False,
            )
            root = pathlib.Path(directory)
            apt = (root / "apt").read_text() if (root / "apt").exists() else ""
            service = (root / "service").read_text() if (root / "service").exists() else ""
            return result, apt, service

    def test_old_installed_packages_are_upgraded(self):
        result, apt, service = self.run_scenario("old")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("php7.4-fpm", apt)
        self.assertIn("php7.4-readline", apt)
        self.assertNotIn("php7.4-imagick", apt)
        self.assertEqual(service, "restart php7.4-fpm\n")

    def test_missing_fpm_is_installed(self):
        result, apt, service = self.run_scenario("missing")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("php7.4-fpm", apt)
        self.assertEqual(service, "restart php7.4-fpm\n")

    def test_fixed_revision_is_accepted_without_upgrade(self):
        result, apt, service = self.run_scenario("patched")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(apt, "")
        self.assertEqual(service, "restart php7.4-fpm\n")

    def test_unpatched_candidate_is_rejected_after_apt_success(self):
        result, apt, service = self.run_scenario("stale-candidate")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("install -y", apt)
        self.assertIn("CVE-2026-109618, CVE-2026-109619", result.stderr)
        self.assertEqual(service, "")

    def test_apt_failure_aborts_before_worker_restart(self):
        result, _, service = self.run_scenario("apt-failure")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(service, "")


if __name__ == "__main__":
    unittest.main()
