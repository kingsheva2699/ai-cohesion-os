#!/usr/bin/env python3
"""Exercise a handoff with invented notes and isolated per-run state. No network."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

HERE=Path(__file__).resolve().parent


def main():
    with tempfile.TemporaryDirectory(prefix="handoff-demo-") as tmp:
        work=Path(tmp).resolve(); project=work/"lantern"; project.mkdir()
        env={**os.environ, "COHESION_RESUME_STATE":str(work/"cards"),
             "COHESION_PICKUP_PROFILES":str(work/"profiles.json")}
        def cli(script,*args,code=0):
            run=subprocess.run([sys.executable,"-B",str(HERE/script),*map(str,args)],cwd=work,
                               env=env,encoding="utf8",capture_output=True,timeout=30)
            if run.returncode!=code:raise RuntimeError(run.stdout or run.stderr)
            return json.loads(run.stdout)
        def resume(*args,code=0):return cli("resume.py",project,"--json",*args,code=code)
        (project/"plan.md").write_text("Decision: Keep the sample counts locally.\nNext: Generate counts.json.\nReview the counts before sharing them.\n",encoding="utf8")
        (project/"items.csv").write_text("item\nlamp\nbook\n",encoding="utf8")
        spec=work/"expected.json"; spec.write_text(json.dumps({"output":"counts.json","inputs":["items.csv"],"checks":{"/count":2},"next_source":"plan.md#L3","next_text":"Review the counts before sharing them."}),encoding="utf8")
        d=resume("--discover"); resume("--review",d["inventory"],"--reviewer","demo reviewer","--rule","plan.md#L1","--next","plan.md#L2","--cite","plan.md#L3")
        cli("pickup.py","add","--id","lantern","--label","Lantern sample","--root",project,"--topic","lantern")
        resume("--begin",spec)
        # Independent, toy producer. The handoff itself never executes a project step.
        import csv
        with (project/"items.csv").open(encoding="utf8") as f: count=sum(1 for _ in csv.DictReader(f))
        with (project/"counts.json").open("x",encoding="utf8") as f:json.dump({"count":count},f)
        result=resume("--finish"); fresh=resume()
        if fresh!=result or fresh["next"][0]["text"]!="Review the counts before sharing them.":raise RuntimeError("Unexpected replay")
        print(cli("pickup.py","show","--id","lantern")["text"])
        (project/"meeting.md").write_text("A new meeting note needs checking.\n",encoding="utf8")
        changed=resume(code=2)
        if changed["changes"]["added"]!=["meeting.md"] or "next" in changed:raise RuntimeError("Expected hold")
        print("Changed source: meeting.md. Handoff withheld pending review.")
    return 0

if __name__=="__main__":raise SystemExit(main())
