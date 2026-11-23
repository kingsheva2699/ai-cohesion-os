"""Local contract tests; use Python's unittest, no model or network required."""
import contextlib
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
import resume


class Handoff(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.base=Path(self.tmp.name); self.root=self.base/'one'; self.root.mkdir()
        self.note=self.root/'record.md'; self.note.write_text('Decision: Owner approved the west desk.\nNext: Match the blue records.\n',encoding='utf8')
        self.state=self.base/'state'; self.ext=self.base/'decision-detail.md'; self.reg=self.base/'projects.json'
        self.row={'id':'one','name':'Project One','aliases':['First'],'status':'active','canonicalPath':str(self.note),'relatedDocs':[],'nextAction':'Review the sample first; then decide.'}
        self.regwrite([self.row]); self.orbit=['--registry',str(self.reg),'--project','First']; self.picks=['--rule','record.md#L1','--next','record.md#L2']
    def regwrite(self,rows): self.reg.write_text(json.dumps(rows),encoding='utf8')
    def runcli(self,*rest):
        stream=io.StringIO()
        with contextlib.redirect_stdout(stream): code=resume.main([str(self.root),'--topic','handoff','--state-dir',str(self.state),'--json',*map(str,rest)])
        return code,json.loads(stream.getvalue())
    def held(self,*rest):
        code,out=self.runcli(*rest); self.assertEqual((code,out['mode']),(2,'hold'),out);self.assertFalse({'rule','next'}&out.keys());return out
    def rev(self,*args):
        code,out=self.runcli('--discover',*args);self.assertEqual(code,0,out)
        return ['--review',out['inventory'],'--reviewer','source checker']
    def saved(self):
        code,out=self.runcli(*self.rev(),*self.picks); self.assertEqual(code,0,out);return out
    def registered(self,*flags):
        args=self.orbit+list(flags);rc,out=self.runcli(*args,*self.rev(*args),'--rule','record.md#L1','--next','orbit:one/nextAction'); self.assertEqual(rc,0,out);return out
    def test_empty_state_does_not_guess(self): self.held();self.assertFalse(self.state.exists())
    def test_no_model_on_review_or_replay(self):
        with patch('resume.urllib.request.build_opener',side_effect=AssertionError): self.assertEqual(self.saved(),self.runcli()[1])
    def test_new_note_invalidates_even_when_existing_lines_match(self):
        self.saved();(self.root/'new.txt').write_text('Replacement pending.');self.held()
    def test_edited_or_removed_note_invalidates(self):
        p=self.root/'other.md';p.write_text('Other evidence');self.saved();p.write_text('Updated evidence');self.held();self.saved();p.unlink();self.held()
    def test_stale_review_digest_is_rejected(self):
        old=self.rev();self.note.write_text('Rule changed\nTask changed');self.held(*old,*self.picks);self.held()
    def test_missing_ref_fails_without_state(self):self.held(*self.rev(),'--rule','outside.md#L1','--next','record.md#L2');self.held()
    def test_question_never_returns_action(self):
        p=self.root/'second.md';p.write_text('Owner approved the east desk.');refs=['--question','Which desk is in force?','--cite','record.md#L1','--cite','second.md#L1'];rev=self.rev();self.held(*rev,*refs,*self.picks);rc,c=self.runcli(*rev,*refs);self.assertEqual((rc,c['mode']),(0,'clarify'));self.assertNotIn('next',self.runcli()[1]);self.assertEqual(len(c['sources']),2)
    def test_citation_tampering(self):
        self.saved();p=next(self.state.glob('*.json'));c=json.loads(p.read_text());c['rule'][0]['text']='Other content';p.write_text(json.dumps(c));self.held()
    def test_invalid_state(self):
        self.saved();next(self.state.glob('*.json')).write_text('[]');self.held()
    def test_path_guard(self):self.held('--state-dir',self.root/'state','--discover')
    def test_private_and_fixtures_omitted(self):
        for d in ('fixtures','.git','secrets'):
            pp=self.root/d;pp.mkdir();(pp/'x.md').write_text('Next: excluded marker')
        rc,d=self.runcli('--discover');self.assertEqual(d['notes_scanned'],1);self.assertNotIn('excluded marker',str(d))
    def test_markdown_decision_table(self):
        (self.root/'table.md').write_text('## Decisions\n| Date | Decision | Source | Confidence |\n|---|---|---|---|\n| Monday | Use green tags | meeting | high |');out=self.runcli('--discover')[1];self.assertTrue(any(x['source']=='table.md#L4' for x in out['decisions']))
    def test_changed_registry_action_holds(self):
        self.registered();self.row['nextAction']='Replacement step.';self.regwrite([self.row]);self.held(*self.orbit)
    def test_unrelated_registry_edit_keeps_card(self):
        before=self.registered();self.regwrite([self.row,dict(self.row,id='two',name='Project Two',aliases=[])]);self.assertEqual(self.runcli(*self.orbit)[1],before)
    def test_duplicate_alias_holds(self):
        self.regwrite([self.row,dict(self.row,id='two')]);self.held('--discover',*self.orbit)
    def test_wrong_root_and_partial_name_hold(self):
        self.held('--discover','--registry',self.reg,'--project','Fir');self.row['canonicalPath']=str(self.base);self.regwrite([self.row]);self.held('--discover',*self.orbit)
    def test_registry_field_required(self):self.held(*self.orbit,*self.rev(*self.orbit),*self.picks)
    def test_pending_status_cannot_resume(self):
        self.row['status']='paused';self.regwrite([self.row]);self.held(*self.orbit,*self.rev(*self.orbit),'--rule','record.md#L1','--next','orbit:one/nextAction')
    def test_missing_related_source_holds(self):
        self.row['relatedDocs']=[str(self.ext)];self.regwrite([self.row]);self.held('--discover',*self.orbit);self.held('--discover',*self.orbit,'--include-note',self.ext)
    def test_only_declared_external_notes(self):
        self.ext.write_text('Decision: same desk policy.');self.row['relatedDocs']=[str(self.ext)];self.regwrite([self.row]);self.registered('--include-note',self.ext);self.held(*self.orbit,'--include-note',self.ext,'--include-note',self.base/'unrelated.md');self.ext.write_text('Replacement: second rule.');self.held(*self.orbit,'--include-note',self.ext)
    def test_oversize_does_not_return_partial_inventory(self):
        with patch.object(resume,'MAX_FILE',8):self.held('--discover')
    def test_failed_draft_is_never_persisted(self):
        with patch('resume.draft',side_effect=resume.Hold('unsupported output')):self.held('--draft');self.held();self.assertFalse(self.state.exists())

if __name__=='__main__': unittest.main()
