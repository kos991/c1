"""Update status must reflect component and service failures."""
import os
import pathlib
import re
import subprocess
import tempfile
import unittest

if os.name == 'nt':
    raise unittest.SkipTest('Update status tests require Bash')

CLIENT = pathlib.Path(__file__).resolve().parents[1] / 'client'
FUNCTION = re.search(r'^updateGWD\(\)\{\n.*?^\}', CLIENT.read_text(encoding='utf-8'), re.M | re.S).group(0)
CONNECT = 'de_GWDconnect(){\n' + CLIENT.read_text(encoding='utf-8').split('de_GWDconnect(){\n', 1)[1].split('\npreInstall(){', 1)[0].strip()


class UpdateStatus(unittest.TestCase):
    def scenario(self, connectivity=0, nginx_active=True, nginx_valid=True):
        with tempfile.TemporaryDirectory() as directory:
            config = pathlib.Path(directory, '0conf')
            config.write_text('{}')
            code = FUNCTION.replace('/opt/de_GWD/0conf', str(config))
            script = '''RED='' GREEN='' WHITE='' cRES=''
cleanDep(){ :; }
preUpdate(){ :; }
de_GWDconnect(){ return CONNECT_STATUS; }
phpVersionForDebian(){ echo 8.4; }
systemctl(){ [[ $3 != nginx || ACTIVE_OK == yes ]]; }
nginx(){ [[ VALID_OK == yes ]]; }
'''.replace('CONNECT_STATUS', str(connectivity)).replace('ACTIVE_OK', 'yes' if nginx_active else 'no').replace('VALID_OK', 'yes' if nginx_valid else 'no')
            # systemctl receives: is-active --quiet <service>
            return subprocess.run(['bash', '-s'], input=script + code + '\nupdateGWD\n', text=True, capture_output=True)

    def test_upstream_failure_does_not_report_success(self):
        result = self.scenario(connectivity=1)
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn('Updated', result.stdout)

    def test_nginx_config_failure_does_not_report_success(self):
        result = self.scenario(nginx_valid=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn('Updated', result.stdout)

    def test_nginx_service_failure_does_not_report_success(self):
        result = self.scenario(nginx_active=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn('Updated', result.stdout)

    def test_healthy_update_reports_success(self):
        result = self.scenario()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('Updated', result.stdout)

    def test_component_failure_propagates_out_of_connected_update(self):
        setup = '''RED='' GREEN='' WHITE='' BLUE='' cRES=''
curl(){ printf 'HTTP/1.1 200 OK\\n'; }
systemctl(){ echo active; }
preDL(){ :; }
updateGWD_Green(){ return 5; }
updateGWD_Red(){ return 6; }
'''
        result = subprocess.run(['bash', '-c', setup + CONNECT + '\nde_GWDconnect u\n'],
                                input='n', text=True, capture_output=True)
        self.assertEqual(result.returncode, 1)
        self.assertNotIn('Updated', result.stdout)
