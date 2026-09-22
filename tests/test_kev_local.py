"""Mock-response tests only: these do not measure a Kev model or Apple GPU."""
import argparse
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

SCRIPT = Path(__file__).resolve().parents[1] / 'skills' / 'kev-local' / 'scripts' / 'kev_local.py'
spec = importlib.util.spec_from_file_location('kev_local', SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class FakeClient:
    timeout = 15.0
    def __init__(self, fail=False, malformed=False):
        self.fail = fail
        self.malformed = malformed
        self.calls = []
    def request(self, path, payload=None, timeout=None):
        self.calls.append((path, payload))
        if self.fail:
            raise mod.KevError('mock_server_failure')
        if path == '/v1/models':
            return {'models': [{'id': 'kev-latest', 'run': 'mock-checkpoint',
                                'base': 'mock-base', 'device': 'mock', 'temperature': 2.0}]}, 1.0
        if self.malformed:
            return {'answers': {}}, 1.0
        important = 'important' in payload['state']['document']['path']
        return {'answers': {
            'relevance': {'type': 'score', 'score': 1.8 if important else 0.1, 'confidence': 0.8,
                          'probabilities': {'0': 0.05, '1': 0.1, '2': 0.85} if important
                          else {'0': 0.95, '1': 0.05, '2': 0.0}},
            'counterevidence': {'type': 'noul', 'noul': 0.1},
        }, 'latency_ms': 10}, 12.0


class Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        for name in ('important.md', 'other.md', 'third.md', 'fourth.md'):
            (self.root / name).write_text('Synthetic short document about ' + name, encoding='utf-8')
        self.manifest = self.root / 'candidates.txt'
        self.manifest.write_text('important.md\nother.md\nthird.md\nfourth.md\n', encoding='utf-8')
        self.args = argparse.Namespace(root=str(self.root), files_from=str(self.manifest),
            required=[], top_k=1, max_candidates=12, max_chars=2400,
            max_file_bytes=524288, budget_seconds=15, query='synthetic test task')
    def tearDown(self):
        self.tmp.cleanup()
    def test_local_url_normalizes(self):
        self.assertEqual(mod.local_url('http://localhost:8009/'), 'http://127.0.0.1:8009')
    def test_remote_and_credentialed_urls_blocked(self):
        for u in ('https://api.typesafe.ai', 'http://example.org:8009',
                  'http://127.0.0.1:8009/v1', 'http://u:p@127.0.0.1:8009',
                  'http://127.0.0.1:8009?x=1', 'file:///tmp/x'):
            with self.subTest(u=u), self.assertRaises(mod.KevError):
                mod.local_url(u)
    def test_redirect_blocked(self):
        with self.assertRaises(mod.KevError):
            mod.NoRedirect().redirect_request(None, None, 302, None, None, 'http://example.org')
    def test_example_validates(self):
        p = SCRIPT.parents[1] / 'examples' / 'decision.json'
        self.assertEqual(mod.validate_request(mod.json_file(str(p)))['model'], 'kev-latest')
    def test_rank_uses_mock_scores_without_returning_all_text(self):
        c = FakeClient()
        r = mod.rank(self.args, c)
        self.assertEqual(r['mode'], 'rank_advisory')
        self.assertEqual(r['suggested_paths'], ['important.md'])
        self.assertEqual(r['inference_calls'], 4)
        self.assertEqual(len(r['deferred_paths']), 3)
        self.assertNotIn('Synthetic short document', json.dumps(r))
        self.assertEqual(r['loaded_model']['run'], 'mock-checkpoint')
    def test_required_documents_not_ranked(self):
        (self.root / 'AGENTS.md').write_text('Required instructions', encoding='utf-8')
        self.args.required = ['other.md']
        c = FakeClient()
        r = mod.rank(self.args, c)
        self.assertIn('other.md', r['suggested_paths'])
        self.assertIn('AGENTS.md', r['suggested_paths'])
        self.assertEqual(r['inference_calls'], 3)
    def test_small_set_skips_every_http_call(self):
        self.args.top_k = 4
        c = FakeClient()
        r = mod.rank(self.args, c)
        self.assertEqual(r['mode'], 'skipped_small_set')
        self.assertEqual(c.calls, [])
        self.assertNotIn('_text', json.dumps(r))
    def test_failure_retains_all_candidates(self):
        r = mod.rank(self.args, FakeClient(fail=True))
        self.assertEqual(r['mode'], 'fallback_local_search')
        self.assertEqual(len(r['suggested_paths']), 4)
        self.assertEqual(r['deferred_paths'], [])
    def test_malformed_response_falls_back(self):
        r = mod.rank(self.args, FakeClient(malformed=True))
        self.assertEqual(r['mode'], 'fallback_local_search')
    def test_truncated_documents_retained(self):
        (self.root / 'other.md').write_text('x' * 3000, encoding='utf-8')
        r = mod.rank(self.args, FakeClient())
        self.assertIn('other.md', r['suggested_paths'])
        row = next(x for x in r['candidates'] if x['path'] == 'other.md')
        self.assertTrue(row['excerpt_only'])
        self.assertTrue(row['review_required'])
    def test_outside_root_rejected(self):
        self.manifest.write_text('../outside.txt\n')
        with self.assertRaises(mod.KevError):
            mod.collect(self.args)
    def test_dotenv_rejected(self):
        self.manifest.write_text('.env\n')
        (self.root / '.env').write_text('EXAMPLE=synthetic')
        with self.assertRaises(mod.KevError):
            mod.collect(self.args)
    def test_invalid_numeric_answers_rejected(self):
        for v in (float('nan'), float('inf'), -1, 1.1, True, '0.8'):
            with self.subTest(v=v), self.assertRaises(mod.KevError):
                mod.number(v, 0, 1)
    def test_timeout_must_be_positive(self):
        with self.assertRaises(mod.KevError):
            mod.Client('http://127.0.0.1:8009', timeout=-1)

    def test_zero_port_is_not_silently_replaced(self):
        with self.assertRaises(mod.KevError):
            mod.local_url('http://127.0.0.1:0')

    def test_claude_instructions_are_not_ranked(self):
        (self.root / 'CLAUDE.md').write_text('Required instructions', encoding='utf-8')
        c = FakeClient()
        result = mod.rank(self.args, c)
        self.assertEqual(result['suggested_paths'][0], 'CLAUDE.md')
        self.assertEqual(result['inference_calls'], 4)

    def test_suggestions_follow_score_not_manifest_order(self):
        self.manifest.write_text('other.md\nthird.md\nimportant.md\nfourth.md\n')
        self.args.top_k = 2
        result = mod.rank(self.args, FakeClient())
        self.assertEqual(result['suggested_paths'], ['important.md', 'other.md'])

    def test_time_budget_retains_all_candidates(self):
        self.args.budget_seconds = 0.01
        with mock.patch.object(mod.time, 'perf_counter', side_effect=[0, 1, 2]):
            client = FakeClient()
            result = mod.rank(self.args, client)
        self.assertEqual(result['mode'], 'fallback_local_search')
        self.assertEqual(len(result['suggested_paths']), 4)
        self.assertEqual(client.calls, [])

    def test_symlink_cannot_escape_root(self):
        (self.root / 'outside.md').symlink_to(self.root.parent / 'outside.md')
        self.manifest.write_text('outside.md\n')
        with self.assertRaises(mod.KevError):
            mod.collect(self.args)

    def test_non_finite_request_rejected_before_http(self):
        payload = {'state': float('nan'), 'questions': {'q': {'type': 'noul', 'instructions': 'Relevant?'}}}
        with self.assertRaises(mod.KevError):
            mod.validate_request(payload)


if __name__ == '__main__':
    unittest.main()
