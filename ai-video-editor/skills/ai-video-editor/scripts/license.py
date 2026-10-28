#!/usr/bin/env python3
"""AI Video Editor license: one purchase email, activated on one computer (the server decides how many:
LICENSE_MAX_DEVICES, 1). Standard library only, because setup.py imports it before the skill's own Python exists.

  license.py status                 STATUS license OK <email> | MISSING | REVOKED <email> | OFFLINE
  license.py code <email>           asks the server to email a 6-digit code to the buyer
  license.py activate <email> <code>   checks the code, activates this computer, saves ST/license.json
  license.py deactivate             frees this computer's place ("odjavi AI Video Editor sa ovog računara")

How it works:
  - The buyer gives the email they paid with. The server sends a code to it only when that email has a paid
    Studio purchase (studio.aiprofit.rs/api/license/code). Typing the code back proves the inbox is theirs.
  - Activation returns a token for THIS computer. ST/license.json keeps the email, the token, this computer's ID
    and when the server last said yes. The server keeps only a hash of the token.
  - Every setup check (the quiet check at the start of each chat) asks the server whether the token is still good.
    Revoked (a chargeback) or removed (deactivated, or support freed the place) ends the license here too.
  - Offline is fine for GRACE_DAYS after the last yes, so a train ride or a bad connection never stops an edit.
  - The computer ID is a hash of the operating system's own machine ID, so a copied state folder does not carry
    the license to another computer.
  - require() is what the build scripts call: a local check only, no network.

The server address can be pointed elsewhere for testing with AI_VIDEO_EDITOR_LICENSE_URL.
"""
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
import uuid

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import skillenv  # noqa: E402

API = os.environ.get('AI_VIDEO_EDITOR_LICENSE_URL', 'https://studio.aiprofit.rs').rstrip('/')
GRACE_DAYS = 14
TIMEOUT = 8
SUPPORT = 'podrska@vladsdigital.com'


def say(line):
    print(line, flush=True)


def license_file(state=None):
    return os.path.join(state or skillenv.state_dir(), 'license.json')


def _run(cmd):
    kw = {'capture_output': True, 'text': True, 'timeout': 10}
    if os.name == 'nt':
        kw['creationflags'] = getattr(subprocess, 'CREATE_NO_WINDOW', 0)
    try:
        return subprocess.run(cmd, **kw).stdout
    except (OSError, subprocess.SubprocessError):
        return ''


def _machine_id():
    """The operating system's own ID for this computer. It survives reinstalling AI Video Editor, not reinstalling the OS."""
    system = platform.system()
    if system == 'Darwin':
        for line in _run(['/usr/sbin/ioreg', '-rd1', '-c', 'IOPlatformExpertDevice']).splitlines():
            if 'IOPlatformUUID' in line:
                return line.split('=')[-1].strip().strip('"')
    elif system == 'Windows':
        for line in _run(['reg', 'query', r'HKLM\SOFTWARE\Microsoft\Cryptography', '/v', 'MachineGuid']).splitlines():
            if 'MachineGuid' in line:
                return line.split()[-1]
    else:
        for path in ('/etc/machine-id', '/var/lib/dbus/machine-id'):
            try:
                with open(path, encoding='utf-8') as f:
                    got = f.read().strip()
                if got:
                    return got
            except OSError:
                pass
    return None


def device_id(state=None):
    """What the server knows this computer by: a hash, never the machine ID itself."""
    raw = _machine_id()
    if not raw:   # no machine ID to read: a random one kept in the state folder (weaker, but it works)
        path = os.path.join(state or skillenv.state_dir(), '.device')
        try:
            with open(path, encoding='utf-8') as f:
                raw = f.read().strip()
        except OSError:
            raw = ''
        if not raw:
            raw = uuid.uuid4().hex
            with open(path, 'w', encoding='utf-8') as f:
                f.write(raw)
    return hashlib.sha256(f'ai-video-editor:{raw}'.encode()).hexdigest()


def device_name():
    names = {'Darwin': 'Mac', 'Windows': 'Windows'}
    host = platform.node().split('.')[0] or 'računar'
    return f'{host} ({names.get(platform.system(), platform.system())})'


def post(path, body):
    """POST JSON to the license server. Returns (http status, reply dict), or (None, None) when it cannot be reached.
    urllib first; when that fails before any answer (a python.org macOS install has no certificates), the system
    curl, which uses the operating system's own certificates."""
    url = API + path
    data = json.dumps(body).encode()
    req = urllib.request.Request(url, data=data, method='POST',
                                 headers={'Content-Type': 'application/json', 'User-Agent': 'ai-video-editor'})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            return r.status, json.loads(r.read() or b'{}')
    except urllib.error.HTTPError as e:   # the server answered: 4xx with a reason
        try:
            return e.code, json.loads(e.read() or b'{}')
        except ValueError:
            return e.code, {}
    except Exception:
        pass
    curl = shutil.which('curl')
    if not curl:
        return None, None
    try:
        r = subprocess.run([curl, '-sS', '--max-time', str(TIMEOUT), '-X', 'POST',
                            '-H', 'Content-Type: application/json', '-H', 'User-Agent: ai-video-editor',
                            '--data-binary', '@-', '-w', '\n%{http_code}', url],
                           input=data, capture_output=True, timeout=TIMEOUT + 5,
                           **({'creationflags': getattr(subprocess, 'CREATE_NO_WINDOW', 0)} if os.name == 'nt' else {}))
        text, _, code = r.stdout.decode('utf-8', 'replace').rpartition('\n')
        if r.returncode != 0 or not code.strip().isdigit() or code.strip() == '000':
            return None, None
        return int(code), json.loads(text or '{}')
    except (OSError, subprocess.SubprocessError, ValueError):
        return None, None


def load(state=None):
    try:
        with open(license_file(state), encoding='utf-8') as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def save(record, state=None):
    path = license_file(state)
    tmp = path + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(record, f, indent=1)
        f.write('\n')
    os.replace(tmp, path)
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass


def forget(state=None):
    try:
        os.remove(license_file(state))
    except OSError:
        pass


def _fresh(rec):
    return time.time() - rec.get('verified_at', 0) < GRACE_DAYS * 86400


def status(state=None):
    """Ask the server about the saved token. Returns (token, detail): OK, MISSING, REVOKED or OFFLINE."""
    rec = load(state)
    if not rec or not rec.get('token'):
        return 'MISSING', None
    if rec.get('device_id') != device_id(state):   # a state folder copied from another computer
        forget(state)
        return 'MISSING', None
    code, reply = post('/api/license/verify', {'token': rec['token'], 'device_id': rec['device_id']})
    if code is None or code >= 500:
        if rec.get('status') == 'revoked':
            return 'REVOKED', rec.get('email')
        return ('OK', rec.get('email')) if _fresh(rec) else ('OFFLINE', rec.get('email'))
    if reply.get('ok'):
        rec.update(status='ok', verified_at=int(time.time()), email=reply.get('email', rec.get('email')))
        save(rec, state)
        return 'OK', rec['email']
    if reply.get('reason') == 'revoked':
        rec['status'] = 'revoked'
        save(rec, state)
        return 'REVOKED', rec.get('email')
    forget(state)   # the server no longer knows this token: deactivated, or the place was freed by support
    return 'MISSING', None


def status_line(state=None):
    token, detail = status(state)
    if token == 'OK':
        return f'STATUS license OK {detail}'
    if token == 'REVOKED':
        return f'STATUS license REVOKED {detail} -> the purchase for this email is no longer active: stop, send them to {SUPPORT}'
    if token == 'OFFLINE':
        return (f'STATUS license OFFLINE -> no connection to the license server for over {GRACE_DAYS} days: '
                'ask them to connect to the internet and run the setup check again')
    return ('STATUS license MISSING -> before anything else: ask for the email they paid with, then '
            'license.py code <email>, then license.py activate <email> <code>')


def require(state=None):
    """For the build scripts: stop with a clear line when this computer has no active license. No network."""
    rec = load(state)
    ok = bool(rec and rec.get('token') and rec.get('status') == 'ok' and rec.get('device_id') == device_id(state)
              and _fresh(rec))
    if not ok:
        say('STATUS license NOT ACTIVE -> run the setup check (Step 0 in SKILL.md): it activates or renews the license')
        sys.exit(3)


def cmd_code(email):
    code, reply = post('/api/license/code', {'email': email})
    if code is None:
        say('STATUS license code FAILED no internet connection to studio.aiprofit.rs')
        return 1
    if reply.get('ok'):
        say(f'STATUS license code SENT {email.strip().lower()} (valid 15 minutes)')
        return 0
    say(f"STATUS license code FAILED {reply.get('reason', code)} | {reply.get('error', '')}")
    return 1


def cmd_activate(email, code_typed, state=None):
    dev = device_id(state)
    code, reply = post('/api/license/activate', {'email': email, 'code': code_typed, 'device_id': dev,
                                                 'device_name': device_name()})
    if code is None:
        say('STATUS license activate FAILED no internet connection to studio.aiprofit.rs')
        return 1
    if reply.get('ok'):
        save({'email': reply['email'], 'token': reply['token'], 'device_id': dev, 'status': 'ok',
              'verified_at': int(time.time()), 'activated_at': int(time.time())}, state)
        say(f"STATUS license OK {reply['email']} (computer {reply.get('devices')} of {reply.get('max_devices')})")
        return 0
    say(f"STATUS license activate FAILED {reply.get('reason', code)} | {reply.get('error', '')}")
    for d in reply.get('devices') or []:
        say(f"  computer: {d.get('name') or '?'} | activated {d.get('activated_at', '')[:10]} | last used {d.get('last_seen', '')[:10]}")
    return 1


def cmd_deactivate(state=None):
    rec = load(state)
    if not rec:
        say('STATUS license MISSING (nothing to deactivate on this computer)')
        return 0
    code, reply = post('/api/license/deactivate', {'token': rec.get('token', '')})
    if code is None:
        say('STATUS license deactivate FAILED no internet connection: the place stays taken, try again online')
        return 1
    forget(state)
    say('STATUS license DEACTIVATED (this computer no longer counts toward the limit)')
    return 0


def main(argv):
    skillenv.utf8_stdio()
    state = skillenv.state_dir()
    os.makedirs(state, exist_ok=True)
    cmd = argv[0] if argv else 'status'
    if cmd == 'status':
        say(status_line(state))
        return 0
    if cmd == 'code' and len(argv) == 2:
        return cmd_code(argv[1])
    if cmd == 'activate' and len(argv) == 3:
        return cmd_activate(argv[1], argv[2], state)
    if cmd == 'deactivate':
        return cmd_deactivate(state)
    say(__doc__.split('\n\n')[1])
    return 2


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
