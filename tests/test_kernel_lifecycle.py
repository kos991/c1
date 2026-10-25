"""Kernel lifecycle regressions: isolated boot/APT files and mocked package tools.

No kernel packages, host boot files, network, or services are changed.
Run on POSIX with Bash: python3 -m unittest discover -s tests -p test_kernel_lifecycle.py
"""
import os
import pathlib
import shlex
import subprocess
import tempfile
import unittest

if os.name == 'nt':
    raise unittest.SkipTest('Kernel lifecycle regressions require POSIX and Bash')

ROOT = pathlib.Path(__file__).resolve().parents[1]
DEBIAN = '6.12.1-amd64'
XANMOD = '6.12.1-x64v1-xanmod1'
NEWER = '9.0.0-x64v3-xanmod1'


class KernelLifecycle(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = pathlib.Path(self.temp.name)
        source = (ROOT / 'resource/kernel/installkernel').read_text(encoding='utf-8')
        for prefix in ('/etc/', '/boot/', '/lib/modules/', '/run/', '/sys/', '/opt/'):
            source = source.replace(prefix, str(self.root) + prefix)
        self.script = self.root / 'installkernel'
        self.script.write_text(source)
        for directory in ('etc/apt/sources.list.d', 'boot/grub', 'run/systemd/system'):
            (self.root / directory).mkdir(parents=True)
        (self.root / 'etc/os-release').write_text('ID=debian\nVERSION_CODENAME=bookworm\n')
        for release in (DEBIAN, XANMOD, NEWER):
            self.image(release)
        (self.root / 'boot/grub/grub.cfg').write_text('grub configuration\n')
        self.log = self.root / 'commands.log'
        self.prelude = r'''
source "$SCRIPT"
RUNNING=6.12.1-amd64
META=linux-xanmod-lts-x64v1
TARGET=6.12.1-x64v1-xanmod1
DEBIAN=6.12.1-amd64
DEBIAN_SOURCE=linux-signed-amd64
DEBIAN_MAINTAINER='Debian Kernel Team <debian-kernel@lists.debian.org>'
IMAGE_STATUS=installed
META_STATUS=installed
IMAGE_VERSION=6.12.1-1
DEBIAN_DEPENDENCY="linux-image-$DEBIAN (= 6.12.1-1)"
XANMOD_DEPENDENCY="linux-headers-$TARGET, linux-image-$TARGET"
FREE_SPACE=9000000
UPDATE_COUNT=0
UPDATE_FAIL_AT=0
INSTALL_FAIL=0
record() { printf '%s\n' "$*" >>"$LOG"; }
uname() { printf '%s\n' "$RUNNING"; }
cpuLevel() { echo 1; }
dpkg() {
    case $1 in
        --print-architecture) echo amd64;;
        --compare-versions) command dpkg "$@";;
        *) return 1;;
    esac
}
dpkg-query() {
    local format=${2#-f=} package=${3:-}
    case $format in
        '${binary:Package} ${db:Status-Status}\n')
            printf '%s installed\n' "linux-image-$DEBIAN" "linux-image-$TARGET" \
                linux-image-9.0.0-x64v3-xanmod1 "$META" linux-image-amd64;;
        '${db:Status-Status}')
            case $package in
                "$META") echo "$META_STATUS";;
                "linux-image-$TARGET") echo "$IMAGE_STATUS";;
                "linux-image-$DEBIAN"|linux-image-amd64|linux-image-9.0.0-x64v3-xanmod1) echo installed;;
                *) return 1;;
            esac;;
        '${Version}') echo "$IMAGE_VERSION";;
        '${Depends}')
            case $package in
                "$META") echo "$XANMOD_DEPENDENCY";;
                linux-image-amd64) echo "$DEBIAN_DEPENDENCY";;
                *) return 1;;
            esac;;
        '${db:Status-Status}|${source:Package}|${Maintainer}')
            [[ $package = "linux-image-$DEBIAN" ]] || return 1
            printf 'installed|%s|%s\n' "$DEBIAN_SOURCE" "$DEBIAN_MAINTAINER";;
        *) return 1;;
    esac
}
apt-cache() { printf 'Candidate: 6.12.1-1\n'; }
apt-get() {
    record "apt-get $*"
    if [[ $1 = update ]]; then
        UPDATE_COUNT=$((UPDATE_COUNT + 1))
        [[ $UPDATE_COUNT != "$UPDATE_FAIL_AT" ]]
        return
    fi
    [[ $INSTALL_FAIL = 0 ]] || return 1
    if [[ $* = *"--reinstall"* && ${!#} = "linux-image-$DEBIAN" ]]; then
        mkdir -p "$SANDBOX/lib/modules/$DEBIAN"
        printf 'repaired image\n' >"$SANDBOX/boot/vmlinuz-$DEBIAN"
    fi
}
apt-mark() { record "apt-mark $*"; }
update-initramfs() {
    record "update-initramfs $*"
    printf 'initrd\n' >"$SANDBOX/boot/initrd.img-${!#}"
}
update-grub() {
    record update-grub
    printf '%s\n' "$SANDBOX"/boot/vmlinuz-* >"$SANDBOX/boot/grub/grub.cfg"
}
systemd-detect-virt() { return 1; }
dkms() { [[ ${DKMS_PRESENT:-0} = 1 ]] && echo 'custom/1, installed'; return 0; }
df() { printf 'Filesystem 1024-blocks Used Available Capacity Mounted\nfixture 99999999 0 %s 0%% /\n' "$FREE_SPACE"; }
confirm() { return 0; }
curl() { [[ $* = *https://dl.xanmod.org/archive.key* ]] || return 1; printf key >"${!#}"; }
gpg() { [[ $4 = -o ]] || return 1; printf key >"$5"; }
reboot() { record FORBIDDEN_REBOOT; return 99; }
shutdown() { record FORBIDDEN_SHUTDOWN; return 99; }
'''

    def image(self, release):
        (self.root / 'boot' / ('vmlinuz-' + release)).write_text('image\n')
        (self.root / 'boot' / ('initrd.img-' + release)).write_text('initrd\n')
        (self.root / 'lib/modules' / release).mkdir(parents=True, exist_ok=True)

    def run_shell(self, body, success=True):
        environment = dict(os.environ, SCRIPT=str(self.script), SANDBOX=str(self.root), LOG=str(self.log))
        result = subprocess.run(['bash', '-s'], input=self.prelude + '\n' + body + '\n',
                                text=True, capture_output=True, env=environment)
        if success:
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        else:
            self.assertNotEqual(result.returncode, 0, result.stderr + result.stdout)
        return result

    def commands(self):
        return self.log.read_text() if self.log.exists() else ''

    def test_selected_lts_dependency_wins_over_newer_installed_mainline(self):
        self.run_shell('installKernel')
        commands = self.commands()
        self.assertIn('update-initramfs -u -k ' + XANMOD, commands)
        self.assertNotIn('update-initramfs -u -k ' + NEWER, commands)
        self.assertIn('apt-mark manual linux-xanmod-lts-x64v1 linux-image-' + XANMOD, commands)
        source = (self.root / 'etc/apt/sources.list.d/c1-xanmod.list').read_text()
        self.assertIn('https://deb.xanmod.org bookworm main', source)
        self.assertIn('signed-by=', source)
        self.assertTrue((self.root / 'etc/apt/keyrings/c1-xanmod.gpg').is_file())
        self.assertNotIn('purge', commands)
        self.assertNotIn('autoremove', commands)
        self.assertNotIn('FORBIDDEN', commands)
        self.assertTrue((self.root / 'boot' / ('vmlinuz-' + NEWER)).exists())

    def test_source_survives_repository_refresh_failure(self):
        self.run_shell('UPDATE_FAIL_AT=2\ninstallKernel', success=False)
        self.assertTrue((self.root / 'etc/apt/sources.list.d/c1-xanmod.list').exists())

    def test_source_survives_package_install_failure(self):
        self.run_shell('apt-get() { record "apt-get $*"; [[ ${!#} != "$META" ]]; }\ninstallKernel', success=False)
        self.assertTrue((self.root / 'etc/apt/sources.list.d/c1-xanmod.list').exists())

    def test_missing_selected_image_does_not_validate_unrelated_image(self):
        (self.root / 'boot' / ('vmlinuz-' + XANMOD)).unlink()
        self.run_shell('installKernel', success=False)
        self.assertNotIn('update-initramfs', self.commands())

    def test_unconfigured_dependency_is_rejected(self):
        self.run_shell('IMAGE_STATUS=unpacked\ninstallKernel', success=False)
        self.assertNotIn('update-initramfs', self.commands())

    def test_ambiguous_or_missing_direct_dependency_is_rejected(self):
        for dependency in ('linux-headers-6.12',
                           'linux-image-' + XANMOD + ', linux-image-' + NEWER,
                           'linux-image-' + XANMOD + ' | linux-image-' + NEWER):
            with self.subTest(dependency=dependency):
                self.run_shell('XANMOD_DEPENDENCY=' + shlex.quote(dependency) + '\ninstalledImageDependency "$META"', success=False)

    def test_restore_repairs_missing_boot_files_with_low_space_and_dkms(self):
        for path in (self.root / 'boot').glob('*'):
            if path.is_file():
                path.unlink()
        (self.root / 'boot/grub/grub.cfg').unlink()
        self.run_shell('RUNNING=unknown-custom\nFREE_SPACE=1\nDKMS_PRESENT=1\nrestoreDebian')
        commands = self.commands()
        self.assertIn('install --no-remove --reinstall -y linux-image-amd64', commands)
        self.assertIn('install --no-remove --reinstall -y linux-image-' + DEBIAN, commands)
        self.assertIn('update-initramfs -c -k ' + DEBIAN, commands)
        self.assertNotIn('apt-mark manual linux-image-unknown-custom', commands)
        self.assertNotIn('purge', commands)
        self.assertTrue((self.root / 'boot' / ('vmlinuz-' + DEBIAN)).exists())

    def test_versioned_dependency_must_be_satisfied(self):
        self.run_shell('IMAGE_VERSION=6.12.0-1\ninstalledImageDependency linux-image-amd64', success=False)

    def test_restore_allows_secure_boot_debian_recovery(self):
        variables = self.root / 'sys/firmware/efi/efivars'
        variables.mkdir(parents=True)
        (variables / 'SecureBoot-fixture').write_bytes(b'\0\0\0\0\1')
        self.run_shell('restoreDebian')
        self.assertIn('update-initramfs', self.commands())

    def test_install_rejects_secure_boot(self):
        variables = self.root / 'sys/firmware/efi/efivars'
        variables.mkdir(parents=True)
        (variables / 'SecureBoot-fixture').write_bytes(b'\0\0\0\0\1')
        self.run_shell('installKernel', success=False)
        self.assertEqual(self.commands(), '')

    def test_install_still_requires_space(self):
        self.run_shell('FREE_SPACE=1\ninstallKernel', success=False)
        self.assertEqual(self.commands(), '')

    def test_restore_rejects_non_debian_dependency(self):
        self.run_shell('DEBIAN_SOURCE=custom-linux\nrestoreDebian', success=False)
        self.assertNotIn('update-initramfs', self.commands())

    def test_remove_requires_running_verified_debian_kernel(self):
        for running in ('unknown-custom', XANMOD, '9.0-custom-amd64'):
            with self.subTest(running=running):
                self.run_shell('RUNNING=' + shlex.quote(running) + '\nremoveXanmod', success=False)
        self.assertEqual(self.commands(), '')

    def test_remove_rejects_custom_package_with_debian_shaped_name(self):
        self.run_shell('DEBIAN_SOURCE=custom-linux\nremoveXanmod', success=False)
        self.assertEqual(self.commands(), '')

    def test_remove_requires_intact_running_fallback_files(self):
        (self.root / 'boot' / ('initrd.img-' + DEBIAN)).unlink()
        self.run_shell('removeXanmod', success=False)
        self.assertEqual(self.commands(), '')

    def test_remove_on_verified_debian_ignores_install_space_and_dkms_gates(self):
        self.run_shell('FREE_SPACE=1\nDKMS_PRESENT=1\nremoveXanmod')
        commands = self.commands()
        purge = next(line for line in commands.splitlines() if 'purge' in line)
        self.assertIn('APT::Get::AutomaticRemove=false', purge)
        self.assertNotIn('linux-image-' + DEBIAN, purge)
        self.assertIn('linux-image-' + XANMOD, purge)
        self.assertNotIn('FORBIDDEN', commands)
        self.assertTrue((self.root / 'boot' / ('vmlinuz-' + DEBIAN)).exists())


if __name__ == '__main__':
    unittest.main()
