"""Read one explicitly selected Orbit row, without following its external paths."""
import hashlib
import json
import os
from pathlib import Path
import re
import unicodedata


def norm(value):
    return ' '.join(unicodedata.normalize('NFKC', value).casefold().split())


def select(registry, query, root):
    """Return the exact registered nextAction and a digest bound to the authorized root."""
    location = registry.expanduser().resolve(strict=True)
    if location.stat().st_size > 16_000_000:
        raise ValueError('Registry exceeds size limit.')
    with location.open('rb') as stream:
        raw = stream.read(16_000_001)
    if len(raw) > 16_000_000:
        raise ValueError('Registry exceeds size limit.')
    rows = json.loads(raw.decode('utf-8-sig'))
    if not isinstance(rows, list) or not all(isinstance(row, dict) for row in rows):
        raise ValueError('Unexpected registry format.')
    needle = norm(query)
    def names(row):
        aliases = row.get('aliases', [])
        if not isinstance(aliases, list): raise ValueError('Invalid registry aliases.')
        return [norm(v) for v in [row.get('id'), row.get('name'), *aliases] if isinstance(v,str) and v.strip()]
    hits = [r for r in rows if needle and needle in names(r)]
    if len(hits) != 1:
        raise ValueError('No unique exact project ID, name or alias. Specify the project ID; do not guess.')
    row = hits[0]
    ident = row.get('id','')
    if not isinstance(ident,str) or not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9._-]{0,149}',ident):
        raise ValueError('Invalid project ID.')
    dest=row.get('canonicalPath') or row.get('path')
    if not isinstance(dest,str) or not Path(dest).is_absolute():raise ValueError('Missing absolute registry destination.')
    destination=Path(dest).resolve(strict=True)
    if destination!=root and not (root in destination.parents and destination.is_file()):
        raise ValueError('This registry project does not match the selected project directory.')
    action=row.get('nextAction')
    if not isinstance(action,str) or not action.strip() or len(action)>2400 or len(action.splitlines())!=1:
        raise ValueError('Selected registry row has no usable single-line nextAction.')
    # Whole selected row, not just the quotation: a change to status, dependencies, or
    # scope must trigger review. Unrelated rows are never served and do not invalidate it.
    binding=[os.path.normcase(str(location)),row]
    digest=hashlib.sha256(json.dumps(binding,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
    related = row.get('relatedDocs', [])
    if not isinstance(related, list) or not all(isinstance(v, str) and Path(v).is_absolute() for v in related):
        raise ValueError('Malformed related-document list.')
    return {'id':ident, 'ref':'orbit:'+ident+'/nextAction', 'text':action, 'digest':digest,
            'document':destination.relative_to(root).as_posix() if destination!=root else '',
            'related':related, 'status':str(row.get('status','')).casefold()}
