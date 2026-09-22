"""Exercise the installed CLI contract against a loopback HTTP fixture, without weights."""
import copy
import json
import os
import subprocess
import sys
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from test_kev_local import SCRIPT, mod


REQUEST = mod.json_file(str(SCRIPT.parents[1] / 'examples' / 'decision.json'))
RESPONSE = {
    'answers': {
        'relevant': {'type': 'noul', 'noul': 0.91},
        'category': {'type': 'choice', 'choice': 'payment', 'confidence': 0.85,
                     'probabilities': {'payment': 0.90, 'ui': 0.05, 'unknown': 0.05}},
        'relevance_level': {'type': 'score', 'score': 1.8, 'confidence': 0.9,
                            'probabilities': {'0': 0.05, '1': 0.1, '2': 0.85},
                            'legend': {'0': 'none', '1': 'background', '2': 'direct'}},
    },
    'latency_ms': 4,
}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_POST(self):
        payload = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        self.server.requests.append((self.path, payload))
        mode = self.server.mode
        if mode == 'slow':
            time.sleep(0.1)
        if mode == 'redirect':
            self.send_response(302)
            self.send_header('Location', '/unexpected')
            self.end_headers()
            return
        self.send_response(422 if mode == 'error' else 200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        result = copy.deepcopy(RESPONSE)
        if mode == 'bad_answer':
            result['answers']['category']['choice'] = 'unrequested'
        body = b'not-json PRIVATE_INPUT' if mode in {'invalid_json', 'error'} else json.dumps(result).encode()
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            pass


class HttpTests(unittest.TestCase):
    def setUp(self):
        self.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        self.server.mode = 'ok'
        self.server.requests = []
        self.thread = threading.Thread(target=self.server.serve_forever, kwargs={'poll_interval': 0.01}, daemon=True)
        self.thread.start()
        self.url = 'http://127.0.0.1:' + str(self.server.server_port)

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()

    def cli(self, *args, timeout='2'):
        env = dict(os.environ, HTTP_PROXY='http://127.0.0.1:1', http_proxy='http://127.0.0.1:1')
        result = subprocess.run(
            [sys.executable, str(SCRIPT), '--base-url', self.url, '--timeout', timeout,
             'ask', '--request', '-', *args],
            input=json.dumps(REQUEST), text=True, capture_output=True, env=env, timeout=5,
        )
        return result, json.loads(result.stdout)

    def test_stdin_all_types_one_request_and_no_input_echo(self):
        process, output = self.cli()
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertEqual(output['mode'], 'live_api')
        self.assertEqual(output['answers']['category']['choice'], 'payment')
        self.assertNotIn('legend', output['answers']['relevance_level'])
        self.assertNotIn(REQUEST['state']['document'], process.stdout)
        self.assertEqual(len(self.server.requests), 1)
        self.assertEqual(self.server.requests[0][0], '/v1/systemone')
        self.assertEqual(self.server.requests[0][1]['model'], 'kev-latest')

    def test_raw_preserves_full_response(self):
        process, output = self.cli('--raw')
        self.assertEqual(process.returncode, 0)
        self.assertEqual(output['response'], RESPONSE)

    def test_errors_have_exit_two_and_no_retry_or_body_leak(self):
        for mode, expected in [('error', 'http_422'), ('invalid_json', 'invalid_json_response'),
                               ('redirect', 'redirect_blocked'), ('bad_answer', 'invalid_choice_answer')]:
            with self.subTest(mode=mode):
                self.server.mode = mode
                self.server.requests.clear()
                process, output = self.cli()
                self.assertEqual(process.returncode, 2, process.stderr)
                self.assertEqual(output['error'], expected)
                self.assertNotIn('PRIVATE_INPUT', process.stdout)
                self.assertEqual(len(self.server.requests), 1)

    def test_timeout_returns_fallback_without_retry(self):
        self.server.mode = 'slow'
        process, output = self.cli(timeout='0.02')
        self.assertEqual(process.returncode, 2)
        self.assertEqual(output['error'], 'local_connection_failed_or_timed_out')
        self.assertEqual(len(self.server.requests), 1)


class AnswerTests(unittest.TestCase):
    def test_invalid_answer_shapes_rejected(self):
        for field, value in [('noul', True), ('noul', float('nan')), ('noul', -0.1)]:
            response = copy.deepcopy(RESPONSE)
            response['answers']['relevant'][field] = value
            with self.subTest(value=value), self.assertRaises(mod.KevError):
                mod.validate_answers(REQUEST, response)
        for qid, field, value in [
            ('category', 'probabilities', {'payment': 0.4, 'ui': 0.1, 'unknown': 0.1}),
            ('category', 'probabilities', {'payment': 1.0}),
            ('category', 'type', 'score'),
            ('category', 'confidence', 1.1),
            ('relevance_level', 'score', 3),
        ]:
            response = copy.deepcopy(RESPONSE)
            response['answers'][qid][field] = value
            with self.subTest(qid=qid, field=field), self.assertRaises(mod.KevError):
                mod.validate_answers(REQUEST, response)

    def test_api_rounding_is_accepted(self):
        response = copy.deepcopy(RESPONSE)
        response['answers']['category']['probabilities'] = dict.fromkeys(['payment', 'ui', 'unknown'], 0.33)
        self.assertEqual(mod.validate_answers(REQUEST, response), response['answers'])


if __name__ == '__main__':
    unittest.main()
