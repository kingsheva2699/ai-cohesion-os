"""Completion state transitions and stale-source explanations for resume.py."""
import contextlib
import json
import os
from pathlib import Path


class ProgressError(ValueError):
    pass


def difference(previous, current, cited, files, resolve):
    if not isinstance(previous, dict):
        return {'detail_available': False, 'review': 'Legacy card lacks file-level fingerprints; review the source set.'}
    before, after = set(previous), set(current)
    edits = sorted(n for n in before & after if previous[n] != current[n])
    refs = {k: [] for k in ('unchanged', 'changed_or_missing')}
    for item in cited:
        try:
            same = resolve(item['source'], files) == item
        except (ValueError, KeyError, TypeError):
            same = False
        refs['unchanged' if same else 'changed_or_missing'].append(item['source'])
    return {'detail_available': True, 'added': sorted(after-before), 'modified': edits,
            'removed': sorted(before-after), 'citations': refs}


def explain_text(changes):
    if not changes.get('detail_available'):
        return changes.get('review', 'File-level comparison unavailable.')
    chunks = []
    for k in ('added','modified','removed'):
        names = changes[k]
        if names:
            chunks.append(k.capitalize()+': '+', '.join(names[:15])+ (' (more in JSON)' if len(names)>15 else ''))
    cites=changes['citations']; n=len(cites['unchanged']); m=len(cites['changed_or_missing'])
    chunks.append(f'Cited references: {n} still match; {m} changed or missing. Review required even if all citations match.')
    return '\n'.join(chunks)


@contextlib.contextmanager
def state_lock(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    lock=path.with_suffix('.write-lock')
    try:
        fd=os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as exc:
        raise ProgressError('Another handoff update is in progress, or its lock needs operator review.') from exc
    try:
        os.close(fd)
        yield
    finally:
        lock.unlink(missing_ok=True)


def task_shape(card):
    return {k:card.get(k) for k in ('version','key','scope_key','topic','mode','rule','next','evidence','question')}


def initial_card(card):
    return {k: card[k] for k in ('version','key','scope_key','inventory','topic','mode','rule','next','evidence','question','reviewer','project') if k in card}


def carry(old, new, replace):
    progress = old.get('progress') if old else None
    if not progress:
        return
    if task_shape(old)==task_shape(new) and not replace:
        new['progress']=progress
    elif not replace:
        raise ProgressError('A previous step has a completion record. Review it and explicitly use --replace-task to retire that proof, rather than repeating the step.')


def display(root, card, ordinary, registry=None):
    p=card.get('progress')
    if not p:
        return ordinary
    if ordinary['mode']!='resume' or p.get('stage') not in {'started','verified'} or task_shape(p['base'])!=task_shape(card):
        raise ProgressError('Completion record is inconsistent with the reviewed task.')
    if p['stage']=='started':
        raise ProgressError('This step was started and has no verified completion yet. Inspect its output and finish verification; do not start it again.')
    import resume_proof
    try:
        v=resume_proof.replay(root,p['base'],p['receipt'],registry=registry)
    except (ValueError,OSError) as exc:
        raise ProgressError('Completion proof no longer verifies. '+str(exc)) from exc
    return {**ordinary, 'completion':{'result':v['result'],'artifact':v['artifact'],'sha256':v['sha256']},
            'next':[v['next']], 'stage':'review', 'waiting_on_you':bool(card.get('waiting_on_you'))}


def advance(kind, root, card, specfile=None, registry=None):
    import resume_proof
    p=card.get('progress'); base=initial_card(card)
    if card.get('mode')!='resume':raise ProgressError('Clarification cards cannot record completed work.')
    try:
        if kind=='begin':
            if p:raise ProgressError('Progress already exists. Do not regenerate an already started or verified step.')
            with Path(specfile).open('rb') as inp: raw=inp.read(32001)
            if len(raw)>32000:raise ProgressError('Proof specification is too large.')
            spec=json.loads(raw.decode('utf-8-sig'))
            if not isinstance(spec,dict) or set(spec)!={'output','inputs','checks','next_source','next_text'}:raise ProgressError('Invalid proof specification fields.')
            ticket=resume_proof.begin(root,base,spec['output'],spec['inputs'],spec['checks'],spec['next_source'],spec['next_text'],registry=registry)
            card['progress']={'stage':'started','base':base,'ticket':ticket}
            return {'mode':'started','topic':card['topic'],'reason':'Input and output expectations recorded. No work was executed.'}
        if not p or p['stage']!='started' or task_shape(p['base'])!=task_shape(card):raise ProgressError('No matching unfinished step to verify.')
        receipt=resume_proof.finish(root,p['base'],p['ticket'],registry=registry)
        card['progress']={'stage':'verified','base':p['base'],'receipt':receipt}
    except (ValueError,OSError) as exc:
        raise ProgressError(str(exc)) from exc
    return None
