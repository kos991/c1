"""Update entry points must reject the wrong role before changing the host."""
import os
import pathlib
import re
import subprocess
import tempfile
import unittest

if os.name == 'nt':
    raise unittest.SkipTest('Update role checks require POSIX and Bash')

ROOT = pathlib.Path(__file__).resolve().parents[1]


class UpdateRole(unittest.TestCase):
    def check_role(self, installer, client_config, server_version, accepted):
        with tempfile.TemporaryDirectory() as directory:
            config = pathlib.Path(directory)
            if client_config:
                (config / '0conf').write_text('{}')
            if server_version:
                (config / 'version.php').write_text('v2.0.0\n')
            source = (ROOT / installer).read_text(encoding='utf-8')
            function = re.search(r'^updateGWD\(\)\{\n.*?^\}', source, re.M | re.S).group(0)
            function = function.replace('/opt/de_GWD/', directory + '/')
            # Stop at the first mutating step; rejected roles must never reach it.
            setup = 'cleanDep(){ echo MUTATION_REACHED; exit 42; }\npreUpdate(){ echo MUTATION_REACHED; exit 42; }\n'
            result = subprocess.run(['bash', '-s'], input=setup + function + '\nupdateGWD\n',
                                    text=True, capture_output=True)
            self.assertEqual(result.returncode, 42 if accepted else 1, result.stderr)
            self.assertEqual('MUTATION_REACHED' in result.stdout, accepted)

    def test_client_accepts_config_even_with_stray_server_version(self):
        self.check_role('client', True, True, True)

    def test_client_accepts_normal_installation(self):
        self.check_role('client', True, False, True)

    def test_client_rejects_server_and_uninstalled_host(self):
        for marker in (False, True):
            with self.subTest(server_version=marker):
                self.check_role('client', False, marker, False)

    def test_server_rejects_client_even_with_server_version(self):
        self.check_role('server', True, True, False)

    def test_server_accepts_server_installation(self):
        self.check_role('server', False, True, True)

    def test_server_rejects_uninstalled_host(self):
        self.check_role('server', False, False, False)
