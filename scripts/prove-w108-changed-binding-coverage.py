#!/usr/bin/env python3
from __future__ import annotations
import argparse, ast, csv, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
INV=ROOT/'docs/canonical/CALAMUS_W108_CHANGED_BINDING_INVENTORY.tsv'
def call_bindings(path):
    src=path.read_text(encoding='utf-8'); tree=ast.parse(src); out={}
    for n in ast.walk(tree):
        if not isinstance(n,ast.Call) or not isinstance(n.func,ast.Name) or n.func.id not in {'bind','bind_toggle'} or not n.args: continue
        a=n.args[0]
        if isinstance(a,ast.Constant) and isinstance(a.value,str): out[a.value]=ast.get_source_segment(src,n) or ''
    return out
def callable_fields(path):
    tree=ast.parse(path.read_text(encoding='utf-8')); out={}
    for c in tree.body:
        if isinstance(c,ast.ClassDef):
            for x in c.body:
                if isinstance(x,ast.AnnAssign) and isinstance(x.target,ast.Name):
                    a=ast.unparse(x.annotation)
                    if 'Callable' in a: out[(c.name,x.target.id)]=a
    return out
def compmap(path,cf):
    src=path.read_text(encoding='utf-8'); tree=ast.parse(src); out={}
    for n in ast.walk(tree):
        if not isinstance(n,ast.Call) or not isinstance(n.func,ast.Name) or not n.func.id.endswith('CompositionInput'): continue
        cls=n.func.id
        for kw in n.keywords:
            if kw.arg and (cls,kw.arg) in cf: out[(cls,kw.arg)]=ast.get_source_segment(src,kw.value) or ''
    return out
rows=list(csv.DictReader(INV.read_text(encoding='utf-8').splitlines(),delimiter='\t'))
ap=argparse.ArgumentParser(); ap.add_argument('--baseline',type=Path); args=ap.parse_args()
if not rows: raise SystemExit('W108_CHANGED_BINDING_COVERAGE=FAIL empty inventory')
for r in rows:
    for k in ('kind','binding_id','baseline','package','payload','owner','adapter','primary_authority','receipt'):
        if not r[k].strip(): raise SystemExit(f"W108_CHANGED_BINDING_COVERAGE=FAIL empty {r['binding_id']} {k}")
keys=[(r['kind'],r['binding_id']) for r in rows]
if len(keys)!=len(set(keys)): raise SystemExit('W108_CHANGED_BINDING_COVERAGE=FAIL duplicate rows')
cmd_rows={r['binding_id'] for r in rows if r['kind']=='COMMAND'}
if len(cmd_rows)!=117: raise SystemExit(f'W108_CHANGED_BINDING_COVERAGE=FAIL command rows={len(cmd_rows)} expected=117')
if args.baseline:
    b=args.baseline.resolve(); old=call_bindings(b/'calamus/calamus_application_commands.py'); new=call_bindings(ROOT/'calamus/calamus_application_commands.py')
    changed={k for k in set(old)|set(new) if old.get(k)!=new.get(k)}
    if changed!=cmd_rows: raise SystemExit(f'W108_CHANGED_BINDING_COVERAGE=FAIL command inventory mismatch {sorted(changed^cmd_rows)}')
    cf=callable_fields(ROOT/'calamus/calamus_application_components.py')
    oldc=compmap(b/'calamus/calamus_application_composition.py',cf); newc=compmap(ROOT/'calamus/calamus_application_composition.py',cf)
    changedc={f'{c}.{f}' for (c,f) in set(oldc)|set(newc) if oldc.get((c,f))!=newc.get((c,f))}
    invc={r['binding_id'] for r in rows if r['kind']=='COMPOSITION'}
    if changedc!=invc: raise SystemExit(f'W108_CHANGED_BINDING_COVERAGE=FAIL composition inventory mismatch {sorted(changedc^invc)}')
nav=[r for r in rows if r['kind']=='COMMAND' and r['binding_id']=='navigate.navigator-panel']
navc=[r for r in rows if r['kind']=='COMPOSITION' and r['binding_id']=='NavigatorCompositionInput.on_visibility_changed']
if len(nav)!=1 or nav[0]['primary_authority']!='BEHAVIORAL-GTK' or 'W108_NAVIGATOR_PANEL_TRUE_GTK' not in nav[0]['receipt']: raise SystemExit('W108_CHANGED_BINDING_COVERAGE=FAIL navigator command authority')
if len(navc)!=1 or navc[0]['primary_authority']!='BEHAVIORAL-GTK': raise SystemExit('W108_CHANGED_BINDING_COVERAGE=FAIL navigator composition authority')
e2e=(ROOT/'tests/test_w108_thin_gtk_shell_app_desktop_e2e.py').read_text(encoding='utf-8')
if e2e.count('window.invoke_command("navigate.navigator-panel"')<2 or 'W108_NAVIGATOR_PANEL_TRUE_GTK=PASS' not in e2e: raise SystemExit('W108_CHANGED_BINDING_COVERAGE=FAIL exact navigator GTK receipt absent')
w101=(ROOT/'tests/test_w101_core_composition_app_desktop_e2e.py').read_text(encoding='utf-8')
if 'window.navigator_panel_runtime.set_visible(True)' not in w101: raise SystemExit('W108_CHANGED_BINDING_COVERAGE=FAIL historical W101 Navigator receipt weakened')
if not any(r['kind']=='GTK_SIGNAL' and r['binding_id']=='CharacterMapDialog.character-button.clicked' for r in rows): raise SystemExit('W108_CHANGED_BINDING_COVERAGE=FAIL Character Map signal inventory missing')
print(f"W108_CHANGED_BINDING_COVERAGE=PASS rows={len(rows)} commands={len(cmd_rows)} composition={sum(r['kind']=='COMPOSITION' for r in rows)}")
