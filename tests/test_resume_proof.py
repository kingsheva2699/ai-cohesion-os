"""Proof API contract. All inputs, cards, and outputs are synthetic, in temporary directories."""
import copy
import hashlib
import json
import os
from pathlib import Path
import stat
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import resume_proof as proof


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def load_again(obj):
    return json.loads(json.dumps(obj))


class Proof(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.base = Path(temp.name).resolve()
        self.root = self.base / 'project'
        self.root.mkdir()
        self.output = self.root / 'out.json'
        self.input = self.root / 'source.csv'
        self.input.write_bytes(b'sample,1\n')
        self.next = {'source': 'tasks.md#L2', 'text': 'Make the example; then inspect the sample rows.'}
        self.cont = {'source': self.next['source'], 'text': 'inspect the sample rows'}
        self.rule = {'source': 'rules.md#L3', 'text': 'Keep the sample on this machine.'}
        self.evidence = {'source': 'tasks.md#L4', 'text': 'Compare both sample totals.'}
        self.card = {'topic': 'Example', 'key': 'example-task', 'inventory': 'example-inventory',
                     'project': {'id': 'example'}, 'next': [self.next], 'rule': [self.rule],
                     'evidence': [self.evidence]}
        self.args = dict(output_rel='out.json', inputs=['source.csv'], checks={'/ok': True},
                         next_source=self.cont['source'], next_text=self.cont['text'])

    def begin(self, **changes):
        return proof.begin(self.root, self.card, **{**self.args, **changes})

    def finish(self, ticket, **kwargs):
        return proof.finish(self.root, self.card, ticket, **kwargs)

    def replay(self, receipt, **kwargs):
        return proof.replay(self.root, self.card, receipt, **kwargs)

    def test_round_trip_and_no_side_effects(self):
        initial = self.input.read_bytes()
        ticket = load_again(self.begin())
        self.assertFalse(self.output.exists())
        with self.assertRaisesRegex(ValueError, 'missing'):
            self.finish(ticket)
        raw = b'{"ok":true,"unexamined":2}\n'
        self.output.write_bytes(raw)
        receipt = load_again(self.finish(ticket))
        ticket.clear()  # consuming the original ticket is independent of the receipt
        result = self.replay(receipt)
        self.assertEqual((result['result'], result['artifact'], result['sha256'], result['next']),
                         ('verified', 'out.json', sha(raw), self.cont))
        self.assertEqual(self.input.read_bytes(), initial)
        self.assertEqual(self.output.read_bytes(), raw)
        self.assertEqual(set(self.root.iterdir()), {self.input, self.output})

    def test_refuses_even_matching_preexisting_file_or_directory(self):
        raw = b'{"ok":true}'
        self.output.write_bytes(raw)
        with self.assertRaisesRegex(ValueError, 'already exists'):
            self.begin()
        self.assertEqual(self.output.read_bytes(), raw)
        self.output.unlink()
        self.output.mkdir()
        with self.assertRaises(ValueError):
            self.begin()

    def test_changed_or_missing_finished_output(self):
        t = self.begin()
        self.output.write_bytes(b'{"ok":true}')
        r = self.finish(t)
        for raw in (b'{"ok": true}', b'{"ok":false}', b'not JSON'):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                self.output.write_bytes(raw)
                self.replay(r)
        self.output.unlink()
        with self.assertRaises(ValueError):
            self.replay(r)

    def test_changed_or_missing_input_at_both_stages(self):
        t = self.begin()
        self.output.write_bytes(b'{"ok":true}')
        r = self.finish(t)
        self.input.write_bytes(b'sample,2\n')  # same size
        for change in (False, True):
            if change:
                self.input.unlink()
            for fn, state in ((self.finish, t), (self.replay, r)):
                with self.subTest(missing=change, fn=fn.__name__), self.assertRaises(ValueError):
                    fn(state)

    def test_wrong_project_root_or_changed_review_fails_at_both_stages(self):
        t = self.begin()
        self.output.write_bytes(b'{"ok":true}')
        r = self.finish(t)
        other = self.base / 'clone'
        other.mkdir()
        for p in [self.input, self.output]:
            (other / p.name).write_bytes(p.read_bytes())
        for fn, state in ((proof.finish, t), (proof.replay, r)):
            with self.assertRaises(ValueError):
                fn(other, self.card, state)
            for key in ('key', 'inventory', 'topic', 'next', 'rule', 'evidence', 'project'):
                c = copy.deepcopy(self.card)
                if isinstance(c[key], list):
                    c[key][0]['text'] += ' Changed.'
                else:
                    c[key] = 'different'
                with self.subTest(fn=fn.__name__, field=key), self.assertRaises(ValueError):
                    fn(self.root, c, state)

    def test_stored_v1_key_binds_normalized_topic_and_root_at_begin(self):
        self.card.update(version=1, mode='resume', reviewer='reader', question='', topic='Ｅxample   Task')
        self.card['key'] = sha(json.dumps([1, os.path.normcase(str(self.root)), 'example task'],
                                         separators=(',', ':'), ensure_ascii=False).encode())
        ticket = self.begin()
        self.card['proof_ticket'] = ticket  # operational state is not part of the reviewed identity
        self.output.write_text('{"ok":true}')
        self.finish(ticket)
        other = self.base / 'other'
        other.mkdir()
        (other / self.input.name).write_bytes(self.input.read_bytes())
        with self.assertRaises(ValueError):
            proof.begin(other, self.card, **self.args)

    def test_separate_full_continuations_from_all_reviewed_lists(self):
        later = {'source': 'tasks.md#L5', 'text': 'Record the comparison result.'}
        self.card['next'].append(later)
        self.card['next'][0]['source'] = 'orbit:example/nextAction'
        for row in (self.rule, self.evidence, later):
            with self.subTest(ref=row['source']):
                t = self.begin(next_source=row['source'], next_text=row['text'])
                self.output.write_text('{"ok":true}')
                self.assertEqual(self.replay(self.finish(t))['next'], row)
                self.output.unlink()

    def test_rejects_uncited_ambiguous_or_insubstantial_continuation(self):
        for src, text in [('unknown', self.cont['text']), (self.rule['source'], self.cont['text']),
                          (self.next['source'], 'then ship the rows'), (self.next['source'], 'rows'),
                          (self.next['source'], 'nspect the sample rows'), (self.next['source'], self.next['text']),
                          (self.next['source'], 'inspect  the sample rows')]:
            with self.subTest(text=text, src=src), self.assertRaises(ValueError):
                self.begin(next_source=src, next_text=text)
        self.card['evidence'].append({**self.next, 'text': 'Contradictory citation.'})
        with self.assertRaises(ValueError):
            self.begin()

    def test_non_actionable_or_incomplete_card(self):
        baseline = self.card.copy()
        for edit in ({'mode': 'clarify'}, {'mode': 'draft'}, {'question': 'Which one?'}, {'key': ''},
                     {'rule': []}, {'next': []}, {'evidence': None}, {'inventory': None}):
            self.card = {**baseline, **edit}
            with self.subTest(edit=edit), self.assertRaises(ValueError):
                self.begin()

    def test_checks_are_exact_typed_values_and_pointers_not_searches(self):
        checks = {'/a~1b/~0/0': False, '/a~1b/~0/1': None, '/a~1b/~0/2': 0,
                  '/a~1b/~0/3': 1.5, '/a~1b/~0/4': '1.5', '/': '', '/01': 8}
        row = [False, None, 0, 1.5, '1.5']
        t = self.begin(checks=checks)
        def write(values):
            self.output.write_text(json.dumps({'a/b': {'~': values}, '': '', '01': 8}))
        write(row)
        self.replay(self.finish(t))
        for index, replacement in ((0, 0), (1, ''), (2, False), (2, 0.0), (3, '1.5'), (4, 1.5)):
            with self.subTest(index=index, replacement=replacement), self.assertRaises(ValueError):
                wrong = row.copy()
                wrong[index] = replacement
                write(wrong)
                self.finish(t)
        write(row[:-1])
        with self.assertRaises(ValueError):
            self.finish(t)

    def test_root_scalar_check_and_exact_decimal(self):
        t = self.begin(checks={'': 0.1})
        self.output.write_bytes(b'1e-1')
        self.replay(self.finish(t))
        self.output.write_bytes(b'0.10000000000000000000001')
        with self.assertRaises(ValueError):
            self.finish(t)

    def test_json_must_be_single_unambiguous_finite_and_utf8(self):
        t = self.begin()
        for raw in (b'', b'{}', b'{"other":{"ok":true}}', b'{"ok":true}{}', b'{"ok":1,"ok":true}',
                    b'{"ok":true,"ignored":{"x":0,"\\u0078":0}}', b'{"ok":true,"x":NaN}',
                    b'{"ok":true,"x":Infinity}', b'{"ok":true,"x":"\xff"}', b'[' * 1200 + b']' * 1200):
            with self.subTest(prefix=raw[:20]), self.assertRaises(ValueError):
                self.output.write_bytes(raw)
                self.finish(t)

    def test_missing_is_not_null_and_array_indices_are_canonical(self):
        for pointer in ('/missing', '/a/-1', '/a/01', '/a/-', '/a/+0', '/a/1', '/a/\u0660'):
            t = self.begin(checks={pointer: None})
            self.output.write_text('{"a":[null]}')
            with self.subTest(pointer=pointer), self.assertRaises(ValueError):
                self.finish(t)
            self.output.unlink()

    def test_json_structure_bounds_do_not_count_escaped_string_contents(self):
        t = self.begin()
        self.output.write_text(json.dumps({'ok': True, 'text': '[,{\\"' * 400}))
        self.finish(t)
        for body in ('[' * 65 + '0' + ']' * 65, '[' + '0,' * 100_000 + '0]'):
            self.output.write_text('{"ok":true,"ignored":' + body + '}')
            with self.assertRaisesRegex(ValueError, 'nesting|entries'):
                self.finish(t)

    def test_empty_invalid_and_excessive_specs(self):
        for checks in ({}, [], {'a': 1}, {'/a~': 0}, {'/a~2': 0}, {'/a': []}, {'/a': {}},
                       {'/a': float('nan')}, {'/a': float('inf')}, {'/a': 2 ** 300}, {'/a': 'x' * 2500},
                       {'/a': {'sha256_of': '@registry'}}, {'/a': {'execute': 'anything'}},
                       {'/a' * 33: True}, {'/' + str(i): 0 for i in range(33)}):
            with self.subTest(keys=str(checks)[:20]), self.assertRaises(ValueError):
                self.begin(checks=checks)
        for inputs in ([], 'source.csv', ['source.csv', 'SOURCE.csv'], ['out.json'], ['missing'], ['x'] * 17):
            with self.subTest(inputs=inputs), self.assertRaises(ValueError):
                self.begin(inputs=inputs)

    def test_portable_local_paths_and_sensitive_name_policy(self):
        for name in ('../other.json', 'a/../out.json', './out.json', '/tmp/out.json', 'C:/out.json',
                     'C:out.json', '//host/share.json', 'a\\b.json', 'a//b.json', 'out.json:stream',
                     'a./b.json', '.env.json', 'a/secret.json', 'token-cache.json', 'private/data.json',
                     'CON.json', 'nul .json', 'Lpt9.test.json', '.git/file.json', 'ssh/id_rsa.json'):
            with self.subTest(name=name, role='output'), self.assertRaises(ValueError):
                self.begin(output_rel=name)
            with self.subTest(name=name, role='input'), self.assertRaises(ValueError):
                self.begin(inputs=[name])
        for name in ('not-json.txt', 'missing-dir/out.json'):
            with self.subTest(name=name), self.assertRaises(ValueError):
                self.begin(output_rel=name)

    def test_external_registry_path_and_contents_are_both_pinned(self):
        reg = self.base / 'registry.json'
        raw = b'[{"id":"example"}]'
        reg.write_bytes(raw)
        twin = self.base / 'copy.json'
        twin.write_bytes(raw)
        check = {'/sourceSha256': {'sha256_of': '@registry'}, '/id': 'example'}
        args = dict(inputs=['source.csv', '@registry'], checks=check)
        with self.assertRaises(ValueError):
            self.begin(**args)
        t = self.begin(**args, registry=reg)
        self.output.write_text(json.dumps({'id': 'example', 'sourceSha256': '0' * 64}))
        with self.assertRaises(ValueError):
            self.finish(t, registry=reg)
        self.output.write_text(json.dumps({'id': 'example', 'sourceSha256': sha(raw)}))
        r = self.finish(t, registry=reg)
        self.replay(load_again(r), registry=reg)
        for fn, state in ((self.finish, t), (self.replay, r)):
            for path in (twin, None):
                with self.subTest(fn=fn.__name__, missing=path is None), self.assertRaises(ValueError):
                    fn(state, registry=path)
        reg.write_bytes(raw + b' ')
        for fn, state in ((self.finish, t), (self.replay, r)):
            with self.assertRaises(ValueError):
                fn(state, registry=reg)
        self.assertNotIn('registry.json', json.dumps(r))
        self.assertNotIn(self.base.name, json.dumps(r))

    def test_sensitive_root_registry_and_registry_input_alias_collision(self):
        folder = self.base / 'credentials'
        folder.mkdir()
        (folder / 'source.csv').write_bytes(b'example')
        reg = folder / 'sample.json'
        reg.write_text('[]')
        with self.assertRaises(ValueError):
            proof.begin(folder, self.card, **self.args)
        with self.assertRaises(ValueError):
            self.begin(inputs=['@registry'], registry=reg)
        local = self.root / reg.name
        local.write_bytes(reg.read_bytes())
        with self.assertRaises(ValueError):
            self.begin(inputs=[local.name, '@registry'], registry=local)

    def test_no_private_literals_or_absolute_paths_in_state_or_error(self):
        marker = 'fixture-string-not-for-logs'
        local = str(self.base / marker)
        t = self.begin(checks={'/value': local})
        self.output.write_text(json.dumps({'value': marker}))
        with self.assertRaises(ValueError) as err:
            self.finish(t)
        self.output.write_text(json.dumps({'value': local}))
        r = self.finish(t)
        for value in (str(err.exception), json.dumps(t), json.dumps(r), json.dumps(self.replay(r))):
            self.assertNotIn(marker, value)
            self.assertNotIn(self.base.name, value)
        self.output.unlink()
        self.evidence['text'] = 'Check ' + local
        with self.assertRaises(ValueError):
            self.begin(next_source=self.evidence['source'], next_text=self.evidence['text'])

    def test_size_limits_at_read_time(self):
        with patch.object(proof, 'MAX_FILE', 2), self.assertRaises(ValueError):
            self.begin()
        t = self.begin()
        self.output.write_text('{"ok":true}')
        with patch.object(proof, 'MAX_OUTPUT', 2), self.assertRaises(ValueError):
            self.finish(t)

    def test_corrupt_saved_proofs_do_not_return_success(self):
        t = self.begin()
        self.output.write_text('{"ok":true}')
        r = self.finish(t)
        for fn, state, edits in ((self.finish, t, {'checks': {}, 'absent': False, 'artifact': 'b.json'}),
                                 (self.replay, r, {'sha256': '0' * 64, 'ticket': {}})):
            for k, v in edits.items():
                with self.subTest(field=k), self.assertRaises(ValueError):
                    fn({**state, k: v})
            for bad in ({}, [], None, {'kind': 'verified'}):
                with self.assertRaises(ValueError):
                    fn(bad)

    def test_file_hard_links_are_not_regular_independent_artifacts(self):
        t = self.begin()
        target = self.base / 'target.json'
        target.write_text('{"ok":true}')
        try:
            os.link(target, self.output)
        except OSError:
            self.skipTest('hard links unavailable on this filesystem')
        with self.assertRaises(ValueError):
            self.finish(t)
        with self.assertRaises(ValueError):
            self.begin(output_rel='another.json', inputs=['out.json'])

    def test_symlinks_and_dangling_links_never_satisfy_absence_or_read(self):
        t = self.begin()
        target = self.base / 'target.json'
        try:
            self.output.symlink_to(target)
        except OSError:
            self.skipTest('symlink creation unavailable on this filesystem')
        with self.assertRaises(ValueError):
            self.begin()
        target.write_text('{"ok":true}')
        with self.assertRaises(ValueError):
            self.finish(t)
        self.output.unlink()
        folder = self.root / 'redirect'
        folder.symlink_to(self.base, target_is_directory=True)
        for args in ({'inputs': ['redirect/target.json']}, {'output_rel': 'redirect/absent.json'}):
            with self.assertRaises(ValueError):
                self.begin(**args)

    def test_reparse_flag_on_ancestor_rejected_even_if_not_symlink(self):
        folder = self.root / 'redirect'
        folder.mkdir()
        original = Path.lstat
        class Junction:
            st_mode = stat.S_IFDIR
            st_file_attributes = 0x400
        with patch.object(Path, 'lstat', lambda p: Junction() if p == folder else original(p)):
            with self.assertRaisesRegex(ValueError, 'reparse'):
                self.begin(output_rel='redirect/absent.json')


    @unittest.skipUnless(os.name == 'nt', 'Windows junctions only')
    def test_real_windows_junction_rejected_at_finish_replay_and_begin(self):
        import _winapi
        dest = self.base / 'destination'
        dest.mkdir()
        folder = self.root / 'reports'
        folder.mkdir()
        t = self.begin(output_rel='reports/sample.json')
        output = folder / 'sample.json'
        output.write_text('{"ok":true}')
        r = self.finish(t)
        output.rename(dest / output.name)
        folder.rmdir()
        _winapi.CreateJunction(str(dest), str(folder))
        self.addCleanup(folder.rmdir)
        with self.assertRaisesRegex(ValueError, 'reparse'):
            self.finish(t)
        with self.assertRaisesRegex(ValueError, 'reparse'):
            self.replay(r)
        with self.assertRaisesRegex(ValueError, 'reparse'):
            self.begin(output_rel='reports/absent.json')


if __name__ == '__main__':
    unittest.main()
