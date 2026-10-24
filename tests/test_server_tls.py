"""Certificate deployment regressions; run on Debian with OpenSSL and Bash."""
import os
import pathlib
import re
import subprocess
import tempfile
import unittest

SOURCE = (pathlib.Path(__file__).resolve().parents[1] / 'server').read_text(encoding='utf-8')

def function(name):
    return re.search(r'^' + name + r'\(\)\{\n.*?^\}', SOURCE, re.M | re.S).group(0)


class ServerTLS(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = pathlib.Path(self.temporary.name)
        self.cert = self.root / 'cert.pem'
        self.key = self.root / 'key.pem'
        subprocess.run(['openssl', 'req', '-x509', '-newkey', 'rsa:2048', '-nodes',
                        '-keyout', str(self.key), '-out', str(self.cert), '-days', '1',
                        '-subj', '/CN=test.invalid', '-addext', 'subjectAltName=DNS:test.invalid'],
                       check=True, capture_output=True)

    def validate(self, cert=None, key=None, host='test.invalid'):
        return subprocess.run(['bash', '-s', '--', str(cert or self.cert), str(key or self.key), host],
                              input=function('validateSSLCertificate') + '\nvalidateSSLCertificate "$1" "$2" "$3"\n',
                              text=True, capture_output=True).returncode

    def test_valid_matching_certificate(self):
        self.assertEqual(self.validate(), 0)

    def test_empty_certificate_is_rejected(self):
        self.cert.write_text('')
        self.assertNotEqual(self.validate(), 0)

    def test_invalid_certificate_is_rejected(self):
        self.cert.write_text('issuance failed')
        self.assertNotEqual(self.validate(), 0)

    def test_wrong_domain_is_rejected(self):
        self.assertNotEqual(self.validate(host='different.invalid'), 0)

    def test_mismatched_private_key_is_rejected(self):
        other = self.root / 'other.key'
        subprocess.run(['openssl', 'genpkey', '-algorithm', 'RSA', '-pkeyopt', 'rsa_keygen_bits:2048',
                        '-out', str(other)], check=True, capture_output=True)
        self.assertNotEqual(self.validate(key=other), 0)

    def test_failed_or_skipped_issuance_preserves_existing_certificate(self):
        acme = self.root / 'acme'
        live = self.root / 'live'
        acme.mkdir()
        live.mkdir()
        certificate = live / 'de_GWD.cer'
        key = live / 'de_GWD.key'
        certificate.write_bytes(self.cert.read_bytes())
        key.write_bytes(self.key.read_bytes())
        expected = (certificate.read_bytes(), key.read_bytes())
        fake = acme / 'acme.sh'
        fake.write_text('#!/bin/bash\nif [[ $1 = --issue ]]; then exit "$ACME_STATUS"; fi\nprintf overwritten >"$LIVE/de_GWD.cer"\n')
        fake.chmod(0o755)
        candidate = acme / 'test.invalid_ecc'
        candidate.mkdir()
        (candidate / 'fullchain.cer').write_text('')
        (candidate / 'test.invalid.key').write_bytes(self.key.read_bytes())
        code = function('validateSSLCertificate') + '\n' + function('issueSSLCertificate')
        code = code.replace('/root/.acme.sh', str(acme)).replace('/var/www/ssl', str(live))
        code += '\ndomain=test.invalid\nissueSSLCertificate test.invalid -d test.invalid\n'
        for status in (1, 2, 0):
            with self.subTest(acme_status=status):
                env = dict(os.environ, ACME_STATUS=str(status), LIVE=str(live))
                result = subprocess.run(['bash', '-s'], input=code, text=True, env=env, capture_output=True)
                self.assertNotEqual(result.returncode, 0, result.stdout)
                self.assertEqual((certificate.read_bytes(), key.read_bytes()), expected)


if __name__ == '__main__':
    unittest.main()
