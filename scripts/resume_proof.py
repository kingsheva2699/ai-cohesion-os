"""Read-only evidence for a reviewed local JSON deliverable; never run its producer.

begin requires 1..16 explicit input names and 1..32 scalar equality checks.
Use slash-separated relative names; the output directory must already exist.
Declare '@registry' in inputs and pass its local JSON path by keyword on all
three calls to pin that file. {'sha256_of': '@registry'} checks its raw bytes.
Pointers support '', ~0, ~1 and canonical zero-based array indices. Booleans,
integers and fractional/exponent numbers are distinct; decimals compare exactly.

The caller owns trusted local ticket/receipt storage, consumes the ticket on
finish, and must revalidate the reviewed card against the live note inventory.
Checksums detect accidental edits, not forgery. Observations on a quiescent
local filesystem do not establish authorship, continuous history, semantic
adequacy of the chosen checks, or permission to perform the cited next step.
"""
import hashlib
import json
import math
import os
import re
import stat
import unicodedata
from decimal import Decimal, InvalidOperation
from functools import wraps
from pathlib import Path


MAX_INPUTS, MAX_CHECKS = 16, 32
MAX_FILE, MAX_OUTPUT, MAX_REGISTRY = 4_000_000, 2_000_000, 16_000_000
_ALIAS = '@registry'
_DEVICE = re.compile(r'(?:CON|PRN|AUX|NUL|CONIN\$|CONOUT\$|CLOCK\$|(?:COM|LPT)[0-9¹²³])\Z', re.I)
_COMPONENT = re.compile(r'[a-zA-Z0-9][a-zA-Z0-9 ._-]{0,99}\Z')
_SECRET = re.compile(r'(?:^|[. _-])(?:secrets?|credentials?|passwords?|passwd|tokens?|'
                     r'private|api[ _-]?keys?|private[ _-]?keys?|id_(?:rsa|dsa|ecdsa|ed25519)|'
                     r'keystore|env|pem|key|pfx|p12|kdbx)(?:$|[. _-])', re.I)
_ABSPATH = re.compile(r'[A-Za-z]:[/\\]|\\\\|(?:^|[\s`\'"=(\[{])/(?!\s|$)')


class _Hold(ValueError):
    pass


def _require(condition, message):
    if not condition:
        raise _Hold(message)


def _public(fn):
    @wraps(fn)
    def guarded(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except _Hold:
            raise
        except (OSError, ValueError, TypeError, KeyError, IndexError, RecursionError, OverflowError):
            raise _Hold('Cannot verify local evidence; check paths, JSON and saved proof state.') from None
    return guarded


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _digest(value):
    # Bound even malformed in-memory/saved metadata before JSON serialization.
    nodes = chars = 0

    def visit(v, depth):
        nonlocal nodes, chars
        nodes += 1
        _require(nodes <= 4096 and depth <= 24, 'Reduce proof metadata size or nesting.')
        if type(v) is str:
            chars += len(v)
            _require(chars <= 96_000, 'Reduce proof metadata length.')
        elif type(v) is dict:
            for k, val in v.items():
                _require(type(k) is str, 'Use string keys in proof metadata.')
                visit(k, depth + 1)
                visit(val, depth + 1)
        elif type(v) is list:
            for val in v:
                visit(val, depth + 1)
        else:
            _require(v is None or type(v) is bool or type(v) is int and v.bit_length() <= 256
                     or type(v) is float and math.isfinite(v), 'Use bounded JSON proof metadata.')

    visit(value, 0)
    return _sha(json.dumps(value, ensure_ascii=False, separators=(',', ':'), sort_keys=True,
                           allow_nan=False).encode('utf-8'))


def _record(kind, **fields):
    body = dict(kind=kind, **fields)
    return {**body, 'checksum': _digest(body)}


def _unpack(record, kind, fields):
    message = 'Invalid saved ' + kind + '; start a new proof.'
    _require(type(record) is dict and len(record) == len(fields) + 2 and
             record.keys() == fields | {'kind', 'checksum'} and record['kind'] == kind, message)
    body = {k: v for k, v in record.items() if k != 'checksum'}
    _require(type(record['checksum']) is str and _digest(body) == record['checksum'], message)
    return body


def _rel(name):
    if isinstance(name, Path):
        name = name.as_posix()
    msg = 'Choose a short portable relative file name, without hidden, secret or device names.'
    _require(type(name) is str and 0 < len(name) <= 240, msg)
    for part in name.split('/'):
        _require(_COMPONENT.fullmatch(part) and part[-1] not in ' .' and not _SECRET.search(part)
                 and not _DEVICE.fullmatch(part.partition('.')[0].rstrip()), msg)
    return name


def _absolute(value):
    p = Path(value)
    _require(not str(p).replace('\\', '/').startswith('//') and '..' not in p.parts
             and not (p.anchor and not p.is_absolute()), 'Select an explicit local path without traversal.')
    p = p.absolute()
    _require(not str(p).replace('\\', '/').startswith('//') and not any(
        ':' in s or '\x00' in s or s.endswith((' ', '.')) or _DEVICE.fullmatch(s.partition('.')[0].rstrip())
        or (os.name == 'nt' and re.search(r'~[0-9]', s))
        for s in p.parts[1:]), 'Select a local path without streams or device names.')
    # A selected root must not turn a sensitive directory into an innocuous
    # relative input name. /private/{var,tmp} are ordinary macOS temp roots.
    parts = p.parts[2:] if p.parts[:3] in (('/', 'private', 'var'), ('/', 'private', 'tmp')) else p.parts[1:]
    _require(not any(_SECRET.search(s) or s.casefold() in {'.ssh', '.aws', '.gnupg', '.git', '.kube'}
                     for s in parts), 'Select a project or registry outside sensitive directories.')
    return p


def _plain(st):
    _require(not stat.S_ISLNK(st.st_mode) and not getattr(st, 'st_file_attributes', 0) & 0x400,
             'Remove links or reparse points from the selected path.')
    return st


def _directory(path):
    for part in (*reversed(path.parents), path):
        st = _plain(part.lstat())
        _require(stat.S_ISDIR(st.st_mode), 'Use an existing plain project or output directory.')
    return st


def _root(root):
    p = _absolute(root)
    _require(p != p.parent, 'Choose a project directory, not a drive or filesystem root.')
    st = _directory(p)
    return p, _digest([os.path.normcase(str(p)), st.st_dev, st.st_ino])


def _absent(path):
    _directory(path.parent)
    try:
        path.lstat()  # exists() follows dangling links and is not an absence test
    except FileNotFoundError:
        return
    raise _Hold('Output already exists; choose a new absent JSON file. Do not adopt or overwrite it.')


def _read(path, limit):
    _directory(path.parent)
    try:
        before = _plain(path.lstat())
    except FileNotFoundError:
        raise _Hold('Required file is missing; check the declared inputs and expected output.') from None
    def stamp(s):
        _require(stat.S_ISREG(s.st_mode) and s.st_nlink == 1 and s.st_size <= limit,
                 'Select a bounded regular file with no hard links.')
        return (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns)
    expected = stamp(before)
    flags = os.O_RDONLY | getattr(os, 'O_BINARY', 0) | getattr(os, 'O_NOFOLLOW', 0) | getattr(os, 'O_NONBLOCK', 0)
    with os.fdopen(os.open(path, flags), 'rb') as f:
        _require(stamp(os.fstat(f.fileno())) == expected, 'File changed before reading; retry.')
        raw = f.read(limit + 1)
        _require(len(raw) == before.st_size and stamp(os.fstat(f.fileno())) == expected,
                 'File changed while reading; retry.')
    _directory(path.parent)
    _require(stamp(_plain(path.lstat())) == expected, 'File changed while reading; retry.')
    return raw


def _output(name):
    name = _rel(name)
    _require(name.lower().endswith('.json'), 'Select a relative .json output.')
    return name


def _inputs(root, names, output, registry):
    _require(type(names) in (list, tuple) and 1 <= len(names) <= MAX_INPUTS,
             'Declare 1 to 16 explicit input files.')
    seen = {str(root / output).casefold()}
    hashes = {}
    binding = None
    for name in names:
        if name == _ALIAS:
            _require(registry is not None, 'Pass the pinned registry path for @registry.')
            p = _absolute(registry)
            _require(p.suffix.lower() == '.json' and all(not s.startswith('.') for s in p.parts[1:]),
                     'Select a non-sensitive local registry JSON file.')
            _rel(p.name)
            binding = _digest(os.path.normcase(str(p)))
            limit = MAX_REGISTRY
        else:
            name = _rel(name)
            p = root / name
            limit = MAX_FILE
        _require(str(p).casefold() not in seen, 'Use distinct input paths, separate from the output.')
        seen.add(str(p).casefold())
        hashes[name] = _sha(_read(p, limit))
    return hashes, binding


def _line(text, limit):
    return type(text) is str and 0 < len(text) <= limit and text == text.strip() and text.isprintable()


def _task(root, card, source, text):
    _require(type(card) is dict and card.get('mode', 'resume') == 'resume' and not card.get('question'),
             'Use a reviewed task card, not a question or draft.')
    _require(all(_line(card.get(k), 2400) for k in ('key', 'inventory', 'topic')),
             'Re-review the task key, topic and inventory.')
    if 'version' in card:  # resume.record v1 binds its normalized topic to the exact root
        topic = ' '.join(unicodedata.normalize('NFKC', card['topic']).casefold().split())
        _require(type(card['version']) is int and card['version'] == 1 and
                 card['key'] == _digest([1, os.path.normcase(str(root)), topic]),
                 'Review the stored task in its original project directory.')
    _require(_line(source, 512) and _line(text, 2400) and not _ABSPATH.search(source)
             and not _ABSPATH.search(text), 'Choose a single reviewed continuation without absolute paths.')
    lines = {}
    for field in ('next', 'rule', 'evidence'):
        rows = card.get(field)
        _require(type(rows) is list and len(rows) <= 64 and (rows or field == 'evidence'),
                 'Use bounded reviewed rule, next and evidence lists.')
        for row in rows:
            _require(type(row) is dict and _line(row.get('source'), 512) and _line(row.get('text'), 2400),
                     'Re-review malformed cited lines.')
            ref, line = row['source'], row['text']
            _require(lines.setdefault(ref, line) == line, 'Resolve conflicting text at the same citation.')
    line = lines.get(source)
    _require(line is not None and text != card['next'][0]['text'],
             'Choose a separately cited continuation or an excerpt, not the completed step.')
    if text != line:
        _require(len(text) >= 12 and len(re.findall(r'\w+', text)) >= 2 and
                 re.search(r'(?<!\w)' + re.escape(text) + r'(?!\w)', line),
                 'Quote a substantive contiguous excerpt, exactly as reviewed.')
    fields = ('key', 'inventory', 'topic', 'next', 'rule', 'evidence', 'project', 'project_binding',
              'version', 'mode', 'reviewer', 'question')
    return _digest({k: card[k] for k in fields if k in card})


def _tokens(pointer):
    _require(type(pointer) is str and len(pointer) <= 512 and
             (pointer == '' or pointer.startswith('/')) and pointer.count('/') <= 32 and
             not re.search(r'~(?![01])', pointer) and pointer.isprintable() and
             not re.search(r'[A-Za-z]:[/\\]|\\\\', pointer),
             'Use a short literal JSON pointer with valid ~0/~1 escapes.')
    return [s.replace('~1', '/').replace('~0', '~') for s in pointer.split('/')[1:]]


def _checks(checks, inputs):
    _require(type(checks) is dict and 1 <= len(checks) <= MAX_CHECKS, 'Declare 1 to 32 JSON value checks.')
    result = {}
    for pointer, value in checks.items():
        _tokens(pointer)
        if type(value) is dict:
            _require(value == {'sha256_of': _ALIAS} and _ALIAS in inputs,
                     'Declare @registry for the sha256_of check; no other expressions are supported.')
            result[pointer] = {'sha256_of': _ALIAS}
        elif type(value) is str:
            _require(len(value) <= 2400, 'Shorten the expected string value.')
            result[pointer] = {'string_sha256': _sha(value.encode('utf-8'))}
        else:
            _require(value is None or type(value) is bool or type(value) is int and value.bit_length() <= 256
                     or type(value) is float and math.isfinite(value), 'Choose a finite bounded JSON scalar.')
            result[pointer] = value
    return result


def _artifact_json(raw):
    # Limit nesting and allocation *before* entering the recursive JSON parser.
    # Quoted brackets, commas and escaped quotes are string data, not structure.
    quoted = escaped = False
    depth = items = 0
    for byte in raw:
        if quoted:
            if escaped:
                escaped = False
            elif byte == 92:  # backslash
                escaped = True
            elif byte == 34:  # quote
                quoted = False
        elif byte == 34:
            quoted = True
        elif byte in b'[{,':
            items += 1
            depth += byte != 44
            _require(depth <= 64 and items <= 100_000, 'Reduce JSON nesting or the number of entries.')
        elif byte in b']}':
            depth -= 1
            _require(depth >= 0, 'Produce a well-formed JSON document.')

    def pairs(items):
        obj = dict(items)
        _require(len(obj) == len(items), 'Remove duplicate JSON object keys before verification.')
        return obj

    def number(token):
        _require(len(token) <= 100, 'Reduce JSON number length.')
        if '.' not in token and 'e' not in token.lower():
            return int(token)
        # Avoid binary-float rounding (or overflow to infinity) masking a mismatch.
        try:
            return Decimal(token)
        except InvalidOperation:
            raise _Hold('Use a bounded JSON exponent.') from None

    def invalid(_):
        raise _Hold('Use finite JSON numbers, not NaN or Infinity.')

    try:
        return json.loads(raw.decode('utf-8-sig'), object_pairs_hook=pairs, parse_int=number,
                          parse_float=number, parse_constant=invalid)
    except (UnicodeError, json.JSONDecodeError, RecursionError):
        raise _Hold('Produce a single bounded UTF-8 JSON document before verification.') from None


def _assert_checks(document, checks, inputs):
    _require(type(checks) is dict and 1 <= len(checks) <= MAX_CHECKS, 'Restore the reviewed JSON checks.')
    for pointer, expected in checks.items():
        actual = document
        for token in _tokens(pointer):
            if type(actual) is dict and token in actual:
                actual = actual[token]
            elif type(actual) is list and re.fullmatch('0|[1-9][0-9]{0,8}', token) and int(token) < len(actual):
                actual = actual[int(token)]
            else:
                raise _Hold('A checked field is missing or its pointer is invalid; inspect the output locally.')
        if type(expected) is dict and set(expected) == {'string_sha256'}:
            ok = type(actual) is str and _sha(actual.encode('utf-8')) == expected['string_sha256']
        elif expected == {'sha256_of': _ALIAS}:
            ok = type(actual) is str and _ALIAS in inputs and actual == inputs[_ALIAS]
        elif type(expected) is float:
            ok = type(actual) is Decimal and actual == Decimal(str(expected))
        else:
            ok = (expected is None or type(expected) in (bool, int)) and type(actual) is type(expected) and actual == expected
        _require(ok, 'A reviewed JSON value or type does not match; inspect the output locally.')


_TICKET = {'root', 'task', 'artifact', 'inputs', 'registry', 'checks', 'next', 'absent'}


@_public
def begin(root, card, output_rel, inputs, checks, next_source, next_text, *, registry=None):
    """Observe absence and bind a task, explicit inputs, checks and cited continuation."""
    root, root_id = _root(root)
    task = _task(root, card, next_source, next_text)
    output = _output(output_rel)
    hashes, binding = _inputs(root, inputs, output, registry)
    assertions = _checks(checks, hashes)
    _absent(root / output)
    return _record('ticket-v1', root=root_id, task=task, artifact=output, inputs=hashes,
                   registry=binding, checks=assertions, next={'source': next_source, 'text': next_text}, absent=True)


def _observe(root, card, ticket, registry):
    t = _unpack(ticket, 'ticket-v1', _TICKET)
    root, root_id = _root(root)
    _require(t['absent'] is True and t['root'] == root_id, 'Use the original ticket and project directory.')
    nxt = t['next']
    _require(type(nxt) is dict and nxt.keys() == {'source', 'text'} and
             _task(root, card, nxt['source'], nxt['text']) == t['task'], 'Task or inventory changed; re-review it.')
    output = _output(t['artifact'])
    hashes = t['inputs']
    _require(type(hashes) is dict and 1 <= len(hashes) <= MAX_INPUTS, 'Restore the declared input list.')
    current, binding = _inputs(root, list(hashes), output, registry)
    _require(binding == t['registry'] and current == hashes, 'Input bytes or registry path changed; start a new proof.')
    raw = _read(root / output, MAX_OUTPUT)
    _assert_checks(_artifact_json(raw), t['checks'], current)
    return {'result': 'verified', 'artifact': output, 'sha256': _sha(raw), 'next': dict(nxt)}


@_public
def finish(root, card, ticket, *, registry=None):
    """Verify the currently present output; return a JSON-serializable receipt."""
    observed = _observe(root, card, ticket, registry)
    # Detach caller-owned mutable state: consuming/clearing the ticket is safe.
    return _record('receipt-v1', ticket=json.loads(json.dumps(ticket)), sha256=observed['sha256'])


@_public
def replay(root, card, receipt, *, registry=None):
    """Repeat the checks and require exactly the finished bytes, not just equal JSON."""
    r = _unpack(receipt, 'receipt-v1', {'ticket', 'sha256'})
    observed = _observe(root, card, r['ticket'], registry)
    _require(observed['sha256'] == r['sha256'], 'Finished artifact bytes changed; re-review the output.')
    return observed
