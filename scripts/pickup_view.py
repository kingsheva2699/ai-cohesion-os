#!/usr/bin/env python3
"""Optional local graphical pickup view. No server, remote API or telemetry."""
import json
from pathlib import Path
import subprocess
import sys

CLI=Path(__file__).with_name("pickup.py")


def query(*args):
    run=subprocess.run([sys.executable,"-B",str(CLI),*args],capture_output=True,
                       encoding="utf8",timeout=60)
    if run.returncode:raise ValueError("Cannot read the local handoff; refresh and check the project.")
    return json.loads(run.stdout)


def build(root,read=query,copy=None):
    import tkinter as tk
    from tkinter import ttk
    root.title("Project pickup"); root.geometry("820x460")
    root.columnconfigure(0,weight=1); root.rowconfigure(2,weight=1)
    ttl=ttk.Label(root,text="Pick up where I left off"); ttl.grid(row=0,column=0,sticky="w",padx=12,pady=6)
    tree=ttk.Treeview(root,columns=("project","status","result","next","waiting"),show="headings",height=5,selectmode="browse")
    for col,label,width in [("project","Project",150),("status","State",65),("result","Last verified result",135),("next","Next step",310),("waiting","Waiting on you",95)]:
        tree.heading(col,text=label);tree.column(col,width=width,stretch=True)
    tree.grid(row=1,column=0,sticky="nsew",padx=12)
    detail=tk.Text(root,height=10,wrap="word",state="disabled",exportselection=False);detail.grid(row=2,column=0,sticky="nsew",padx=12,pady=6)
    bar=ttk.Frame(root);bar.grid(row=3,column=0,sticky="w",padx=12,pady=6);msg=tk.StringVar()
    def show(text):
        detail.configure(state="normal");detail.delete("1.0","end");detail.insert("end",text);detail.configure(state="disabled")
    def refresh():
        for item in tree.get_children():tree.delete(item)
        show("");msg.set("")
        try:
            for r in read("list")["projects"]:
                tree.insert("","end",iid=r["id"],values=(r["label"],r["status"],r["last_result"],r["next_step"],"Yes" if r["waiting_on_you"] else "—"))
            if not tree.get_children():msg.set("No projects opted in yet. See docs/resume.md.")
        except (OSError,ValueError,KeyError,subprocess.SubprocessError):msg.set("Could not refresh the local list.")
    def selected(copy_now=False):
        ids=tree.selection();show("");msg.set("")
        if len(ids)!=1:return
        try:
            row=read("show","--id",ids[0]);text=row["text"]
            if row["id"]!=ids[0] or tree.selection()!=ids:raise ValueError("Selection changed")
            show(text)
            if copy_now and row["status"] in {"ready","review","clarify"}:
                if copy is None:root.clipboard_clear();root.clipboard_append(text)
                else:copy(text)
                msg.set("Copied only the selected handoff.")
            elif copy_now:msg.set("Handoff on hold. Nothing copied.")
        except (tk.TclError,OSError,ValueError,KeyError,subprocess.SubprocessError):msg.set("Could not read or copy the current handoff.")
    tree.bind("<<TreeviewSelect>>",lambda _e:selected())
    ttk.Button(bar,text="Refresh",command=refresh).pack(side="left");ttk.Button(bar,text="Copy selected handoff",command=lambda:selected(True)).pack(side="left");ttk.Label(bar,textvariable=msg).pack(side="left",padx=8)
    refresh();return tree,selected,msg


def main():
    try:import tkinter as tk
    except ImportError as exc:raise SystemExit("Tk is not installed. Use pickup.py list and show instead.") from exc
    try:root=tk.Tk()
    except tk.TclError as exc:raise SystemExit("No graphical display available. Use pickup.py list and show instead.") from exc
    build(root);root.mainloop()

if __name__=="__main__":main()
