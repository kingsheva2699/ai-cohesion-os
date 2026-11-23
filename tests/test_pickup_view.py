"""Exercise real Tk selection; inject the clipboard sink so tests never overwrite it."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
import pickup_view

class Picker(unittest.TestCase):
    def setUp(self):
        try:
            import tkinter as tk
            self.root=tk.Tk();self.root.withdraw()
        except (ImportError,RuntimeError) as exc:self.skipTest(str(exc))
        except Exception as exc:
            if exc.__class__.__name__=="TclError":self.skipTest("No graphical display")
            raise
        self.addCleanup(self.root.destroy);self.texts=[];self.held=False;self.calls=[]
        def read(*args):
            self.calls.append(args)
            if args==("list",):return {"projects":[dict(id=i,label=i,status="ready",last_result="",next_step="Review sample",waiting_on_you=False) for i in ("amber","blue")]}
            k=args[2];return {"id":k,"status":"hold" if self.held else "review","text":"Changed; review required" if self.held else "Reviewed sample for "+k}
        self.tree,self.select,self.message=pickup_view.build(self.root,read,self.texts.append)
    def test_copy_refetches_and_excludes_the_other_project(self):
        self.tree.selection_set("amber");self.select();self.tree.selection_set("blue");self.select(True)
        self.assertEqual(self.texts,["Reviewed sample for blue"]);self.assertEqual(self.calls[-1],("show","--id","blue"))
    def test_changed_project_is_not_copied(self):
        self.tree.selection_set("amber");self.select();self.held=True;self.select(True)
        self.assertEqual(self.texts,[]);self.assertIn("Nothing copied",self.message.get())
    def test_empty_selection_is_not_copied(self):
        self.select(True);self.assertEqual(self.texts,[])
