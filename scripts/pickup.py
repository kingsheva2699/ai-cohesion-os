#!/usr/bin/env python3
"""Opt-in Project Orbit switcher. list/show are read-only; no public transport."""
import argparse
import contextlib
import io
import json
import os
from pathlib import Path
import re
import sys

import resume
from resume_progress import state_lock

ID = re.compile(r'[a-zA-Z0-9][a-zA-Z0-9._-]{0,119}\Z')


def profile_file():
    loc=Path(os.environ.get('LOCALAPPDATA') or Path.home()/'.local/state')/'CohesionOS'/'pickup-profiles.json'
    return Path(os.environ.get('COHESION_PICKUP_PROFILES') or loc).expanduser().resolve()


def load(path):
    if not path.exists(): return {}
    if path.stat().st_size>150000:raise ValueError('Profile list exceeds its limit.')
    with path.open(encoding='utf8') as stream:profiles=json.load(stream)
    if not isinstance(profiles,dict) or len(profiles)>30:raise ValueError('Invalid profile list.')
    for key,profile in profiles.items():
        if not ID.fullmatch(key) or not isinstance(profile,dict) or not isinstance(profile.get('label'),str) or not Path(profile['root']).is_absolute():raise ValueError('Invalid profile entry.')
    return profiles


def read_one(profile):
    args=[profile['root'],'--topic',profile['topic'],'--json']
    if profile.get('registry'):
        args+=['--registry',profile['registry'],'--project',profile['project']]
        for p in profile['pins']:args+=['--include-note',p]
    if profile.get('state_dir'):args+=['--state-dir',profile['state_dir']]
    out=io.StringIO()
    with contextlib.redirect_stdout(out):rc=resume.main(args)
    card=json.loads(out.getvalue())
    if rc and card.get('mode')!='hold':raise ValueError('Could not read project.')
    return card


def status(c):
    if c['mode']=='resume':return 'review' if c.get('completion') else 'ready'
    return 'clarify' if c['mode']=='clarify' else 'hold'


def summary(key,profile,c):
    st=status(c)
    nxt=' '.join(x['text'] for x in c.get('next',[])) if st in ('ready','review') else c.get('question') or 'Source or completion review needed.'
    proof=c.get('completion',{}); result=('Verified: '+proof['artifact']) if proof.get('artifact') else 'No current verified result.'
    return {'id':key,'label':profile['label'],'status':st,'last_result':str(result)[:220],
            'next_step':nxt[:240],'waiting_on_you':st=='clarify' or c.get('waiting_on_you') is True}


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__); subs=parser.add_subparsers(dest='op',required=True)
    subs.add_parser('list');show=subs.add_parser('show');show.add_argument('--id',required=True)
    add=subs.add_parser('add');add.add_argument('--id',required=True);add.add_argument('--label',required=True);add.add_argument('--root',type=Path,required=True);add.add_argument('--topic',required=True);add.add_argument('--registry',type=Path);add.add_argument('--project');add.add_argument('--include-note',action='append',type=Path,default=[]);add.add_argument('--state-dir',type=Path)
    remove=subs.add_parser('remove');remove.add_argument('--id',required=True)
    a=parser.parse_args(argv);f=profile_file()
    try:
        if a.op!='list' and not ID.fullmatch(a.id):raise ValueError('Invalid project ID.')
        if a.op in {'add','remove'}:
            with state_lock(f):
                profiles=load(f)
                if a.op=='add':
                    if a.id in profiles:raise ValueError('Already opted in; remove explicitly to change its scope.')
                    if len(profiles)>=30:raise ValueError('At most 30 opted-in profiles.')
                    if not a.label.strip() or len(a.label)>120 or not a.topic.strip() or len(a.topic)>200:raise ValueError('Invalid label or topic.')
                    if bool(a.project)!=bool(a.registry) or (a.include_note and not a.registry):raise ValueError('Registry, ID and pins must define an explicit scope.')
                    root=a.root.expanduser().resolve(strict=True)
                    if f==root or root in f.parents:raise ValueError('Keep the opt-in list outside the project.')
                    profile={'root':str(root),'topic':a.topic,'label':a.label.strip(),'registry':str(a.registry.resolve(strict=True)) if a.registry else '', 'project':a.project or '', 'pins':[str(p.resolve(strict=True)) for p in a.include_note],'state_dir':str(a.state_dir.resolve()) if a.state_dir else ''}
                    if read_one(profile)['mode'] not in ('resume','clarify'):raise ValueError('Review this handoff before opting it in.')
                    profiles[a.id]=profile
                else:
                    if a.id not in profiles:raise ValueError('Project is not opted in.')
                    del profiles[a.id]
                resume.save(f,profiles);result={'id':a.id,'opted_in':a.op=='add'}
        else:
            profiles=load(f)
            if a.op=='list':result={'projects':[summary(k,p,read_one(p)) for k,p in sorted(profiles.items())]}
            else:
                if a.id not in profiles:raise ValueError('Project is not opted in.')
                p=profiles[a.id];c=read_one(p);result={'id':a.id,'status':status(c),'text':p['label']+'\n'+resume.format_md(c)}
    except (ValueError,OSError,TypeError,KeyError) as exc:
        print(json.dumps({'error':str(exc) if isinstance(exc,ValueError) else 'Could not verify the local handoff.'}));return 2
    print(json.dumps(result,ensure_ascii=False));return 0

if __name__=='__main__':
    if hasattr(sys.stdout,'reconfigure'):sys.stdout.reconfigure(encoding='utf-8',errors='replace')
    raise SystemExit(main())
