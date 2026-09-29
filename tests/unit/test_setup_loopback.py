"""Real HTTP tests for the temporary loopback owner-setup service."""
from __future__ import annotations

import threading
import urllib.parse

import httpx
import pytest

from deploy.setup_loopback import SetupServer


class Remote:
    public_login = 'https://unit.example.invalid/'

    def __init__(self):
        self.needs = True
        self.passwords = []
        self.fail = False

    def status(self):
        return {'needs_setup': self.needs}

    def setup(self, password):
        if self.fail:
            raise RuntimeError('upstream')
        self.passwords.append(password)
        self.needs = False


@pytest.fixture
def live_server():
    remote = Remote()
    server = SetupServer(remote, port=0, ttl=60)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield remote, server, f'http://{server.expected_host}'
    server.shutdown(); server.server_close(); thread.join(timeout=2)


def form_from(page):
    token = page.split('name="csrf" value="', 1)[1].split('"', 1)[0]
    return {'csrf': token, 'p': 'long-enough-password', 'p2': 'long-enough-password'}


def test_page_and_actual_form_submission(live_server):
    remote, server, url = live_server
    page = httpx.get(url + '/', headers={'Host': server.expected_host})
    assert page.status_code == 200
    assert "default-src 'none'" in page.headers['content-security-policy']
    result = httpx.post(url + '/', data=form_from(page.text), headers={'Origin': url})
    assert result.status_code == 200
    assert remote.passwords == ['long-enough-password']
    assert server.setup_state.done


def test_host_origin_and_csrf_rejected(live_server):
    remote, _server, url = live_server
    assert httpx.get(url + '/', headers={'Host': 'evil.invalid'}).status_code == 403
    page = httpx.get(url + '/')
    data = form_from(page.text)
    assert httpx.post(url + '/', data=data, headers={'Origin': 'http://evil.invalid'}).status_code == 403
    data['csrf'] = 'wrong'
    assert httpx.post(url + '/', data=data, headers={'Origin': url}).status_code == 403
    assert remote.passwords == []


def test_missing_origin_uses_loopback_host_and_one_time_csrf(live_server):
    remote, _server, url = live_server
    page = httpx.get(url + '/')
    data = form_from(page.text)
    result = httpx.post(url + '/', data=data)
    assert result.status_code == 200
    assert remote.passwords == ['long-enough-password']


def test_opaque_origin_requires_full_same_origin_navigation_metadata(live_server):
    remote, _server, url = live_server
    page = httpx.get(url + '/')
    data = form_from(page.text)
    headers = {
        'Origin': 'null', 'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-Mode': 'navigate', 'Sec-Fetch-User': '?1',
        'Sec-Fetch-Dest': 'document',
    }
    assert httpx.post(url + '/', data=data, headers={'Origin': 'null'}).status_code == 403
    assert httpx.post(url + '/', data=data, headers=headers).status_code == 200
    assert remote.passwords == ['long-enough-password']


def test_duplicate_fields_mismatch_and_large_body_rejected(live_server):
    remote, _server, url = live_server
    page = httpx.get(url + '/'); data = form_from(page.text)
    body = urllib.parse.urlencode([('csrf', data['csrf']), ('csrf', data['csrf']), ('p', data['p']), ('p2', data['p2'])])
    assert httpx.post(url + '/', content=body, headers={'Origin': url, 'Content-Type': 'application/x-www-form-urlencoded'}).status_code == 400
    data['p2'] = 'different-password'
    assert httpx.post(url + '/', data=data, headers={'Origin': url}).status_code == 400
    assert httpx.post(url + '/', content=b'x' * 4097, headers={'Origin': url, 'Content-Type': 'application/x-www-form-urlencoded'}).status_code == 413
    assert remote.passwords == []


def test_upstream_failure_never_shows_success(live_server):
    remote, server, url = live_server; remote.fail = True
    page = httpx.get(url + '/')
    result = httpx.post(url + '/', data=form_from(page.text), headers={'Origin': url})
    assert result.status_code == 502
    assert '正式账号密码已设置' not in result.text
    assert not server.setup_state.done


def test_expired_and_already_initialized_rejected(live_server):
    remote, server, url = live_server
    server.setup_state.expires = 0
    assert httpx.get(url + '/').status_code == 410
    remote.needs = False
    server.setup_state.expires = float('inf')
    assert httpx.get(url + '/').status_code == 409
