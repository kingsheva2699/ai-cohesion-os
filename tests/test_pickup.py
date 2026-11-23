"""Fresh-process integration tests for the opted-in board, change explanation and progress."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPTS=Path(__file__).resolve().parents[1]/'scripts'

class Pickup(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(dir=os.environ.get('TMPDIR') or None);self.addCleanup(self.tmp.cleanup)
        self.base=Path(self.tmp.name);self.a=self.base/'amber';self.b=self.base/'blue';self.a.mkdir();self.b.mkdir()
        self.env=dict(os.environ,COHESION_RESUME_STATE=str(self.base/'cards'),COHESION_PICKUP_PROFILES=str(self.base/'opt-in.json'))
        for root in [self.a,self.b]:
            (root/'notes.md').write_text('Decision: Prepare a '+root.name+' report.\nNext: Generate report.json.\nReview the resulting report.\n',encoding='utf8')
            (root/'records.csv').write_text('name\n'+root.name,encoding='utf8')
        self.spec=self.base/'expectation.json';self.spec.write_text(json.dumps({'output':'report.json','inputs':['records.csv'],'checks':{'/status':'ready','/count':1},'next_source':'notes.md#L3','next_text':'Review the resulting report.'}));self.rev(self.a)
    def cli(self,script,*args):
        z=subprocess.run([sys.executable,'-B',str(SCRIPTS/script),*map(str,args)],env=self.env,cwd=self.base,capture_output=True,encoding='utf8',timeout=30)
        self.assertTrue(z.stdout.strip(),z.stderr);return z.returncode,json.loads(z.stdout)
    def resume(self,root,*args):return self.cli('resume.py',root,'--topic','report','--json',*args)
    def board(self,*args):return self.cli('pickup.py',*args)
    def rev(self,root):
        rc,s=self.resume(root,'--discover');self.assertEqual(rc,0,s);rc,c=self.resume(root,'--review',s['inventory'],'--reviewer','fixture','--rule','notes.md#L1','--next','notes.md#L2','--cite','notes.md#L3');return rc,c
    def opt(self,root):
        rc,o=self.board('add','--id',root.name,'--label',root.name,'--root',root,'--topic','report');self.assertEqual(rc,0,o)
    def test_name_changes_and_exact_citations(self):
        (self.a/'meeting.md').write_text('Unrelated meeting note.');rc,c=self.resume(self.a);self.assertEqual(rc,2);self.assertEqual(c['changes']['added'],['meeting.md']);self.assertEqual(len(c['changes']['citations']['unchanged']),3);self.assertNotIn('next',c)
        self.rev(self.a);(self.a/'meeting.md').unlink();f=self.a/'notes.md';f.write_text(f.read_text().replace('Generate','Cancel'));rc,c=self.resume(self.a);self.assertEqual(c['changes']['removed'],['meeting.md']);self.assertEqual(c['changes']['modified'],['notes.md']);self.assertEqual(c['changes']['citations']['changed_or_missing'],['notes.md#L2'])
    def test_board_only_explicit_selection(self):
        self.opt(self.a);self.assertEqual([v['id'] for v in self.board('list')[1]['projects']],['amber']);self.assertNotEqual(self.board('show','--id','blue')[0],0)
        self.rev(self.b);self.opt(self.b);rc,items=self.board('list');self.assertEqual(rc,0);self.assertEqual(len(items['projects']),2)
        rc,one=self.board('show','--id','blue');self.assertIn('blue report',one['text']);self.assertNotIn('amber',str(one));self.assertNotIn('notes.md#L1',str(items));self.assertNotIn('profiles',str(one))
        (self.b/'new.md').write_text('New decision');rc,one=self.board('show','--id','blue');self.assertEqual(one['status'],'hold');self.assertIn('new.md',one['text']);self.assertNotIn('Generate report.json',one['text']);self.assertEqual(self.board('show','--id','amber')[1]['status'],'ready')
    def test_finished_step_does_not_repeat_or_skip_review(self):
        self.opt(self.a);rc,c=self.resume(self.a,'--begin',self.spec);self.assertEqual(rc,0,c);self.assertEqual(self.resume(self.a)[1]['mode'],'hold');self.assertEqual(self.resume(self.a,'--finish')[0],2)
        p=self.a/'report.json';p.write_text(json.dumps({'status':'ready','count':1}));rc,c=self.resume(self.a,'--finish');self.assertEqual(rc,0,c)
        for again in [c,self.resume(self.a)[1]]:
            self.assertEqual(again['next'][0]['text'],'Review the resulting report.');self.assertIn('completion',again);self.assertFalse(again['execution_authorized_by_handoff'])
        self.assertEqual(self.board('list')[1]['projects'][0]['status'],'review');self.assertNotIn('Generate report.json',self.board('show','--id','amber')[1]['text']);self.assertEqual(self.resume(self.a,'--begin',self.spec)[0],2)
        (self.a/'meeting.md').write_text('Unrelated meeting.');self.assertEqual(self.resume(self.a)[0],2);self.assertEqual(self.rev(self.a)[0],0);self.assertEqual(self.resume(self.a)[1]['stage'],'review');p.write_text('{"count": 9}');rc,c=self.resume(self.a);self.assertEqual(rc,2);self.assertNotIn('next',c)
    def test_clarification_marks_waiting_without_suggesting_action(self):
        _,d=self.resume(self.b,'--discover');rc,c=self.resume(self.b,'--review',d['inventory'],'--reviewer','fixture','--question','Which report is approved?','--cite','notes.md#L1');self.assertEqual(rc,0);self.opt(self.b);row=self.board('list')[1]['projects'][0];self.assertTrue(row['waiting_on_you']);self.assertEqual(row['status'],'clarify');self.assertNotIn('Generate',self.board('show','--id','blue')[1]['text'])

if __name__=='__main__':unittest.main()
