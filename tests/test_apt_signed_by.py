"""Debian source trust configuration regressions, using isolated paths."""
import os
import pathlib
import re
import subprocess
import tempfile
import unittest

if os.name == 'nt':
    raise unittest.SkipTest('APT source test requires a POSIX filesystem; run it on Debian')

ROOT = pathlib.Path(__file__).resolve().parents[1]
KEYRING = '/usr/share/keyrings/debian-archive-keyring.gpg'

class DebianSignedBy(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.apt = pathlib.Path(self.temp.name) / 'apt'
        self.sources = self.apt / 'sources.list.d'
        self.sources.mkdir(parents=True)

    def repair(self, installer='server'):
        source = (ROOT / installer).read_text(encoding='utf-8')
        function = re.search(r'^configureDebianSignedBy\(\)\{\n.*?^\}', source, re.M | re.S).group(0)
        function = function.replace('/etc/apt/', str(self.apt) + '/').replace('/usr/share/keyrings/debian-archive-keyring.gpg', str(self.apt / 'debian-archive-keyring.gpg'))
        (self.apt / 'debian-archive-keyring.gpg').write_bytes(b'test-keyring')
        subprocess.run(['bash', '-s'], input='debianCodename=trixie\n' + function + '\nconfigureDebianSignedBy\n',
                       text=True, check=True, capture_output=True)

    def test_list_preserves_options_components_and_existing_signer(self):
        path = self.sources / 'mixed.list'
        original = ('deb [arch=amd64] https://deb.debian.org/debian trixie main non-free-firmware # local\n'
                    'deb-src https://debian.mirror.constant.com trixie main\n'
                    'deb [signed-by=/custom.gpg] https://deb.debian.org/debian trixie-updates main\n'
                    'deb https://download.docker.com/linux/debian trixie stable\n'
                    '# deb https://deb.debian.org/debian trixie main\n')
        path.write_text(original)
        self.repair()
        updated = path.read_text()
        keyring = str(self.apt / 'debian-archive-keyring.gpg')
        expected = original.replace('[arch=amd64]', '[signed-by=' + keyring + ' arch=amd64]').replace(
            'deb-src https://debian.mirror.constant.com', 'deb-src [signed-by=' + keyring + '] https://debian.mirror.constant.com')
        self.assertEqual(updated, expected)
        self.assertEqual(path.with_name(path.name + '.c1-before-signed-by.save').read_text(), original)
        self.repair()
        self.assertEqual(path.read_text(), expected)
        self.assertEqual(path.with_name(path.name + '.c1-before-signed-by.save').read_text(), original)

    def test_deb822_multiline_disabled_and_third_party_stanzas(self):
        path = self.sources / 'multiple.sources'
        debian = ('Types: deb deb-src\nURIs: https://deb.debian.org/debian\n https://debian.mirror.constant.com\n'
                  'Suites: trixie\n trixie-updates\nEnabled: no\nComponents: main contrib non-free-firmware\n')
        custom = ('Types: deb\nURIs: https://deb.debian.org/debian-security/\nSuites: trixie-security\n'
                  'Signed-By: /custom-keyring.gpg\nComponents: main\n')
        third_party = 'Types: deb\nURIs: https://packages.sury.org/php/\nSuites: trixie\nComponents: main\n'
        mixed = 'Types: deb\nURIs: https://deb.debian.org/debian https://example.invalid/debian\nSuites: trixie\nComponents: main\n'
        original = '\n'.join([debian, custom, third_party, mixed])
        path.write_text(original)
        self.repair()
        expected = '\n'.join([debian + 'Signed-By: ' + str(self.apt / 'debian-archive-keyring.gpg') + '\n', custom, third_party, mixed])
        self.assertEqual(path.read_text(), expected)
        self.repair()
        self.assertEqual(path.read_text(), expected)

    def test_all_standalone_installers_repair_security_source(self):
        path = self.sources / 'security.sources'
        original = 'Types: deb\nURIs: https://deb.debian.org/debian-security/\nSuites: trixie-security\nComponents: main\n'
        for installer in ['client', 'server', '@init']:
            with self.subTest(installer=installer):
                path.write_text(original)
                self.repair(installer)
                self.assertEqual(path.read_text(), original + 'Signed-By: ' + str(self.apt / 'debian-archive-keyring.gpg') + '\n')

if __name__ == '__main__':
    unittest.main()
