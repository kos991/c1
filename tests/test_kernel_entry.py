"""Kernel menu must not silently succeed when its download is empty or fails."""
import os
import pathlib
import re
import subprocess
import unittest

if os.name == 'nt':
    raise unittest.SkipTest('Kernel menu tests require Bash')

ROOT = pathlib.Path(__file__).resolve().parents[1]


class KernelMenu(unittest.TestCase):
    def menu(self, role, download):
        source = (ROOT / role).read_text(encoding='utf-8')
        function = re.search(r'^installkernel\(\)\{\n.*?^\}', source, re.M | re.S).group(0)
        setup = '''wget(){ DOWNLOAD; }
'''.replace('DOWNLOAD', download)
        return subprocess.run(['bash', '-s'], input=setup + function + '\ninstallkernel\n',
                              text=True, capture_output=True)

    def test_failed_download_is_an_error_on_both_roles(self):
        for role in ('client', 'server'):
            with self.subTest(role=role):
                result = self.menu(role, 'return 7')
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('download failed', result.stderr)

    def test_empty_download_is_an_error_on_both_roles(self):
        for role in ('client', 'server'):
            with self.subTest(role=role):
                result = self.menu(role, 'return 0')
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('nothing was run', result.stderr)

    def test_corrupt_download_is_not_executed(self):
        for role in ('client', 'server'):
            with self.subTest(role=role):
                result = self.menu(role, '''while [[ $# -gt 0 ]]; do
  if [[ $1 == -O ]]; then shift; printf 'this is not Bash syntax {{{\\n' >"$1"; break; fi
  shift
done''')
                self.assertNotEqual(result.returncode, 0)
