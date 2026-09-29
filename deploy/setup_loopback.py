"""Short-lived loopback form for user-owned, remote owner initialization.

Never sets a local account. Machine/bootstrap credentials remain server-side.
This helper neither logs form data nor forwards upstream cookies to a browser.
"""
from __future__ import annotations

import html
import json
import os
import secrets
import threading
import time
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit

import httpx


@dataclass(repr=False)
class Remote:
    origin: str
    authorization: str
    bootstrap: str
    public_login: str

    def __post_init__(self):
        for value in (self.origin, self.public_login):
            parsed = urlsplit(value)
            if (parsed.scheme != 'https' or not parsed.hostname
                    or not parsed.hostname.endswith('.apigateway-cn-beijing.volceapi.com')
                    or parsed.username or parsed.password or parsed.query or parsed.fragment
                    or parsed.path not in ('', '/') or parsed.port not in (None, 443)):
                raise ValueError('invalid fixed HTTPS endpoint')
        if not self.authorization.startswith('Bearer ') or not self.bootstrap:
            raise ValueError('initialization credentials missing')
        self.origin = self.origin.rstrip('/')

    def status(self):
        response = httpx.get(
            self.origin + '/api/auth/status',
            headers={'Authorization': self.authorization}, timeout=45, follow_redirects=False,
        )
        if response.status_code != 200:
            raise RuntimeError('remote authentication status unavailable')
        body = response.json()
        if type(body.get('needs_setup')) is not bool:
            raise RuntimeError('invalid remote authentication status')
        return body

    def setup(self, password):
        response = httpx.post(
            self.origin + '/api/auth/setup',
            headers={'Authorization': self.authorization, 'Origin': self.public_login.rstrip('/')},
            json={'password': password, 'setup_token': self.bootstrap},
            timeout=45, follow_redirects=False,
        )
        if response.status_code != 200:
            raise RuntimeError('remote initialization rejected')
        body = response.json()
        if body.get('ok') is not True or body.get('username') != 'owner' or body.get('role') != 'owner':
            raise RuntimeError('remote initialization not confirmed')
        # The setup response issues a session; revoke it, never relay it locally.
        cookie = response.cookies.get('wizard_session')
        if cookie:
            logout = httpx.post(
                self.origin + '/api/auth/logout',
                headers={'Authorization': self.authorization, 'Origin': self.public_login.rstrip('/')},
                cookies={'wizard_session': cookie}, timeout=30, follow_redirects=False,
            )
            if logout.status_code != 200:
                raise RuntimeError('initialization session cleanup incomplete')
        if self.status()['needs_setup'] is not False:
            raise RuntimeError('remote owner verification failed')


@dataclass
class SetupState:
    remote: object = field(repr=False)
    expires: float
    nonce: str = field(default_factory=lambda: secrets.token_urlsafe(32), repr=False)
    done: bool = False
    lock: threading.Lock = field(default_factory=threading.Lock, repr=False)


class SetupServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = False

    def __init__(self, remote, port=8799, ttl=600):
        self.setup_state = SetupState(remote=remote, expires=time.monotonic() + ttl)
        super().__init__(('127.0.0.1', port), Handler)
        self.expected_host = f'127.0.0.1:{self.server_port}'
        self.expected_origin = 'http://' + self.expected_host


class Handler(BaseHTTPRequestHandler):
    def setup(self):
        super().setup()
        self.connection.settimeout(10)

    def log_message(self, *args):
        pass  # No URL/form/cookie/credential access logs.

    def send_page(self, code, message):
        raw = message.encode('utf-8')
        self.send_response(code)
        for key, value in {
            'Content-Type': 'text/html; charset=utf-8', 'Content-Length': str(len(raw)),
            'Cache-Control': 'no-store', 'Referrer-Policy': 'no-referrer',
            'X-Content-Type-Options': 'nosniff', 'X-Frame-Options': 'DENY',
            'Content-Security-Policy': "default-src 'none'; style-src 'unsafe-inline'; form-action 'self'; frame-ancestors 'none'; base-uri 'none'",
            'Connection': 'close',
        }.items():
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(raw)
        self.close_connection = True

    def gate(self):
        if self.path != '/':
            self.send_page(404, '页面不存在'); return False
        if self.headers.get_all('Host') != [self.server.expected_host]:
            self.send_page(403, '仅允许本机入口'); return False
        state = self.server.setup_state
        if state.done or time.monotonic() >= state.expires:
            self.send_page(410, '设置窗口已关闭；请返回公网登录。'); return False
        return True

    def do_GET(self):
        if not self.gate():
            return
        try:
            needs_setup = self.server.setup_state.remote.status()['needs_setup']
        except Exception:
            return self.send_page(503, '无法确认线上账号状态，未开放密码设置。')
        if not needs_setup:
            return self.send_page(409, '线上账号已经初始化，请使用公网登录。')
        token = html.escape(self.server.setup_state.nonce, quote=True)
        self.send_page(200, f'''<!doctype html><html lang="zh-CN"><meta charset="utf-8">
<title>设置 AgentKit Wizard 主账号</title>
<body style="margin:0;background:#101419;color:#f6f7f8;font-family:system-ui;padding:48px 20px">
<main style="max-width:460px;margin:auto"><p style="color:#ff794d">AGENTKIT WIZARD</p>
<h1>设置你的登录密码</h1><p>正式用户名：<b>owner</b></p>
<p style="color:#b8c1cd;line-height:1.7">这是仅本机可访问的临时设置页。密码将安全提交到线上服务；请勿在聊天中发送密码。</p>
<form method="post" action="/" enctype="application/x-www-form-urlencoded" autocomplete="off">
<input type="hidden" name="csrf" value="{token}">
<label for="p">新密码（至少 12 位）</label><input id="p" name="p" type="password" minlength="12" maxlength="256" required autocomplete="new-password" style="display:block;box-sizing:border-box;width:100%;padding:13px;margin:10px 0 22px">
<label for="p2">再次输入密码</label><input id="p2" name="p2" type="password" minlength="12" maxlength="256" required autocomplete="new-password" style="display:block;box-sizing:border-box;width:100%;padding:13px;margin:10px 0 22px">
<button type="submit" style="width:100%;padding:14px;background:#fa552f;color:white;border:0;font-size:16px">设置正式账号密码</button>
</form><p style="font-size:13px;color:#b8c1cd">完成后使用公网登录页登录。临时设置服务将自动关闭。</p></main></body></html>''')

    def same_origin_navigation(self):
        origins = self.headers.get_all('Origin') or []
        if origins == [self.server.expected_origin]:
            return True
        # Sandboxed embedded browsers serialize the origin of a plain local
        # form as the opaque value `null`. Accept only when Fetch Metadata proves
        # this is a user-initiated, same-origin, top-level document navigation.
        if origins == ['null']:
            return (
                self.headers.get('Sec-Fetch-Site') == 'same-origin'
                and self.headers.get('Sec-Fetch-Mode') == 'navigate'
                and self.headers.get('Sec-Fetch-User') == '?1'
                and self.headers.get('Sec-Fetch-Dest') == 'document'
            )
        # CLI/older clients may omit Origin; exact loopback Host plus the one-time
        # CSRF nonce remain mandatory, while every explicit foreign origin fails.
        return not origins

    def do_POST(self):
        if not self.gate():
            return
        if not self.same_origin_navigation():
            return self.send_page(403, '请求来源不允许。')
        if self.headers.get('Transfer-Encoding') or len(self.headers.get_all('Content-Length', [])) != 1:
            return self.send_page(400, '请求格式错误。')
        if self.headers.get('Content-Type', '').split(';')[0] != 'application/x-www-form-urlencoded':
            return self.send_page(415, '请求格式错误。')
        try:
            size = int(self.headers.get('Content-Length', '0'))
            if not 0 < size <= 4096:
                return self.send_page(413, '请求大小不允许。')
            raw = self.rfile.read(size)
            if len(raw) != size:
                return self.send_page(400, '请求不完整。')
            form = parse_qs(raw.decode('utf-8'), strict_parsing=True, max_num_fields=3, keep_blank_values=True)
            if set(form) != {'csrf', 'p', 'p2'} or any(len(v) != 1 for v in form.values()):
                raise ValueError('ambiguous form')
        except (TimeoutError, ValueError, UnicodeError):
            return self.send_page(400, '表单格式错误。')
        state = self.server.setup_state
        if not secrets.compare_digest(form['csrf'][0], state.nonce):
            return self.send_page(403, '设置页面已失效，请重新打开。')
        password = form['p'][0]
        if not 12 <= len(password) <= 256 or password != form['p2'][0]:
            return self.send_page(400, '密码至少 12 位，两次输入必须一致。请返回重试。')
        with state.lock:
            if state.done or time.monotonic() >= state.expires:
                return self.send_page(410, '设置窗口已关闭。')
            try:
                if not state.remote.status()['needs_setup']:
                    return self.send_page(409, '账号已经初始化，不能重复设置。')
                state.remote.setup(password)
            except Exception:
                return self.send_page(502, '线上设置未确认成功。请勿重复提交；请检查线上账号状态。')
            state.done = True
            state.nonce = secrets.token_urlsafe(32)
        url = html.escape(state.remote.public_login, quote=True)
        self.send_page(200, f'<html lang="zh-CN"><meta charset="utf-8"><title>主账号设置成功</title><h1>正式账号密码已设置</h1><p>用户名：owner</p><a href="{url}">打开公网登录页</a><p>请使用刚设置的密码登录。</p></html>')
        threading.Thread(target=self.server.shutdown, daemon=True).start()


def serve(remote, port=8799, ttl=600):
    if not remote.status()['needs_setup']:
        raise RuntimeError('owner already initialized')
    server = SetupServer(remote, port, ttl)
    timer = threading.Timer(ttl, server.shutdown)
    timer.daemon = True
    timer.start()
    print(json.dumps({'setup_url': server.expected_origin + '/', 'expires_in_seconds': ttl}), flush=True)
    try:
        server.serve_forever()
    finally:
        timer.cancel()
        server.server_close()


if __name__ == '__main__':
    try:
        serve(Remote(
            os.environ['WIZARD_UPSTREAM_ORIGIN'], os.environ['WIZARD_UPSTREAM_AUTH_VALUE'],
            os.environ['WIZARD_OWNER_SETUP_TOKEN'], os.environ['WIZARD_PUBLIC_LOGIN_URL'],
        ), port=int(os.environ.get('WIZARD_SETUP_PORT', '8799')))
    except Exception:
        raise SystemExit('安全设置服务未启动或已关闭；请检查脱敏预检结果。') from None
