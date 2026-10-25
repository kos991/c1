"""GPT and Claude media routes must survive save, reload, and reset."""
import json
import os
import pathlib
import shutil
import subprocess
import tempfile
import unittest

if os.name == 'nt' or shutil.which('jq') is None or shutil.which('flock') is None:
    raise unittest.SkipTest('AI routing tests require POSIX, jq, and flock')

ROOT = pathlib.Path(__file__).resolve().parents[1] / 'resource' / 'client' / 'ui-script'


class AIRouting(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = pathlib.Path(self.temp.name)
        (self.root / 'vtrui').mkdir()
        nodes = [
            {'domain': 'first.example', 'name': 'First', 'tls': 'first.example', 'uuid': '11111111-1111-4111-8111-111111111111', 'path': '/ws'},
            {'domain': 'second.example', 'name': 'Second', 'tls': 'second.example', 'uuid': '22222222-2222-4222-8222-222222222222', 'path': '/ws'},
        ]
        (self.root / '0conf').write_text(json.dumps({'v2node': nodes, 'v2nodeDIV': {'nodeSM': {}}}))
        (self.root / 'vtrui' / 'config.json').write_text(json.dumps({
            'outbounds': [{'tag': 'default', 'protocol': 'freedom'}, {'tag': 'direct', 'protocol': 'freedom'}],
            'routing': {'rules': []},
        }))
        for name in ('ui-node-lib', 'ui-NodeSM', 'ui-NodeSMcheck'):
            source = (ROOT / name).read_text(encoding='utf-8')
            (self.root / name).write_text(source.replace('/opt/de_GWD', str(self.root)))
        (self.root / 'ui-submitListBWsm').write_text('#!/bin/bash\nexit 0\n')
        (self.root / 'ui-submitListBWsm').chmod(0o755)

    def apply(self, *choices):
        # Keep this fixture independent of the caller's uid/group; check routing
        # semantics, not deployment ownership (which the installer sets).
        command = 'chown(){ :; }; export -f chown; bash "$1" "${@:2}"'
        result = subprocess.run(['bash', '-c', command, 'bash', str(self.root / 'ui-NodeSM'), *choices],
                                text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads((self.root / 'vtrui' / 'config.json').read_text())

    def test_distinct_gpt_claude_and_legacy_openai_routes(self):
        config = self.apply('r', '0', '0', '0', '0', '0', '1', '2', '1', '0', '0')
        tags = [rule['outboundTag'] for rule in config['routing']['rules'] if rule['outboundTag'].startswith('nodeSM')]
        self.assertEqual(tags, ['nodeSMgpt', 'nodeSMopenai', 'nodeSMclaude'])
        endpoints = {outbound['tag']: outbound['settings']['vnext'][0]['address'] for outbound in config['outbounds'] if outbound['tag'].startswith('nodeSM')}
        self.assertEqual(endpoints, {'nodeSMgpt': 'second.example', 'nodeSMopenai': 'first.example', 'nodeSMclaude': 'first.example'})
        self.assertIn('domain:chatgpt.com', config['routing']['rules'][0]['domain'])
        self.assertIn('geosite:openai', config['routing']['rules'][1]['domain'])
        self.assertIn('domain:claude.ai', config['routing']['rules'][2]['domain'])
        self.assertEqual(self.apply()['routing']['rules'], config['routing']['rules'])
        self.assertEqual(json.loads((self.root / '0conf').read_text())['v2nodeDIV']['nodeSM']['status'], 'on')

    def test_gpt_default_falls_back_to_existing_openai_route(self):
        self.apply('r', '0', '0', '0', '0', '0', '1', '2', '1', '0', '0')
        config = self.apply('r', '0', '0', '0', '0', '0', '1', '0', '0', '0', '0')
        media = [rule['outboundTag'] for rule in config['routing']['rules'] if rule['outboundTag'].startswith('nodeSM')]
        self.assertEqual(media, ['nodeSMopenai'])
        state = json.loads((self.root / '0conf').read_text())['v2nodeDIV']['nodeSM']
        self.assertEqual(state['openai'], 'first.example')
        self.assertNotIn('gpt', state)
        self.assertNotIn('claude', state)

    def test_no_argument_rebuild_keeps_default_routes_off(self):
        self.apply('r', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0')
        result = self.apply()
        self.assertEqual(json.loads((self.root / '0conf').read_text())['v2nodeDIV']['nodeSM']['status'], 'off')
        self.assertFalse(any(rule['outboundTag'].startswith('nodeSM') for rule in result['routing']['rules']))

    def test_legacy_apple_rule_is_replaced_with_supported_domains(self):
        path = self.root / 'vtrui' / 'config.json'
        config = json.loads(path.read_text())
        config['routing']['rules'].append({
            'type': 'field', 'outboundTag': 'direct',
            'domain': ['geosite:apple', 'geosite:apple-ads', 'geosite:apple-dev',
                       'geosite:apple-update', 'geosite:icloud', 'geosite:apple@cn', 'geosite:apple-cn'],
        })
        path.write_text(json.dumps(config))
        result = self.apply('r', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0')
        apple = [rule for rule in result['routing']['rules'] if rule['outboundTag'] == 'direct' and 'geosite:apple' in rule.get('domain', [])]
        self.assertEqual(len(apple), 1)
        self.assertNotIn('geosite:apple-ads', apple[0]['domain'])
