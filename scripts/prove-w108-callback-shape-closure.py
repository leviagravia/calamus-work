#!/usr/bin/env python3
from __future__ import annotations
import ast, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMPONENTS = ROOT / 'calamus' / 'calamus_application_components.py'
COMPOSITION_FILES = sorted((ROOT/'calamus').glob('*composition.py'))

def callable_arity(node):
    # Return exact required positional arity for Callable[[...], R], None for non-callable/ellipsis.
    if node is None: return None
    if isinstance(node, ast.Subscript):
        base = node.value
        name = base.id if isinstance(base, ast.Name) else base.attr if isinstance(base, ast.Attribute) else None
        if name == 'Callable':
            sl = node.slice
            if isinstance(sl, ast.Tuple) and sl.elts:
                argspec = sl.elts[0]
                if isinstance(argspec, ast.List):
                    return len(argspec.elts)
                if isinstance(argspec, ast.Constant) and argspec.value is Ellipsis:
                    return None
            return None
    return None

def class_fields(path):
    tree=ast.parse(path.read_text(encoding='utf-8'))
    out={}
    for n in tree.body:
        if isinstance(n, ast.ClassDef):
            fields={}
            for stmt in n.body:
                if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
                    fields[stmt.target.id]=stmt.annotation
            if fields: out[n.name]=fields
    return out

fields=class_fields(COMPONENTS)
rows=[]
all_mapping_count=0
for path in COMPOSITION_FILES:
    tree=ast.parse(path.read_text(encoding='utf-8'))
    parents={}
    for p in ast.walk(tree):
        for c in ast.iter_child_nodes(p): parents[c]=p
    for call in [n for n in ast.walk(tree) if isinstance(n, ast.Call)]:
        direct=[kw for kw in call.keywords if kw.arg is not None and isinstance(kw.value,ast.Attribute) and isinstance(kw.value.value,ast.Name) and kw.value.value.id=='inputs']
        all_mapping_count += len(direct)
        target=call.func.id if isinstance(call.func, ast.Name) else None
        if target not in fields: continue
        cur=call; fn=None
        while cur in parents:
            cur=parents[cur]
            if isinstance(cur,(ast.FunctionDef,ast.AsyncFunctionDef)):
                fn=cur; break
        source_cls=None
        if fn:
            for a in fn.args.args:
                if a.arg=='inputs' and isinstance(a.annotation, ast.Name): source_cls=a.annotation.id
        if source_cls not in fields: continue
        for kw in direct:
            sf=kw.value.attr; tf=kw.arg
            if sf not in fields[source_cls] or tf not in fields[target]: continue
            sa=callable_arity(fields[source_cls][sf]); ta=callable_arity(fields[target][tf])
            if sa is None and ta is None: continue
            rows.append({
                'file':str(path.relative_to(ROOT)), 'source_class':source_cls,'source_field':sf,
                'target_class':target,'target_field':tf,'source_arity':sa,'target_arity':ta,
                'status':'PASS' if sa==ta else 'MISMATCH'
            })

# Explicit W108 shell adapter contract: the root record must expose a bool-shaped Navigator callback.
source=(ROOT/'bin/calamus').read_text(encoding='utf-8')
components=(ROOT/'calamus/calamus_application_components.py').read_text(encoding='utf-8')
composition=(ROOT/'calamus/calamus_application_composition.py').read_text(encoding='utf-8')
explicit = {
    'root_field': 'on_navigator_visibility_changed: Callable[[bool], Any]' in components,
    'root_adapter': 'on_navigator_visibility_changed=lambda _visible: self.refresh_ui_state()' in source,
    'composition_binding': 'on_visibility_changed=inputs.on_navigator_visibility_changed' in composition,
    'no_bad_binding': 'on_visibility_changed=inputs.refresh_ui_state' not in composition,
    'no_variadic_workaround': 'refresh_ui_state(*args)' not in source and 'refresh_ui_state(self, *' not in source,
}

mismatches=[r for r in rows if r['status']!='PASS']
report={'mapping_count':all_mapping_count,'callable_mappings_checked':len(rows),'mismatches':mismatches,'explicit_navigator_adapter':explicit}
print(json.dumps(report,indent=2,sort_keys=True))
if all_mapping_count < 106:
    print(f'W108_CALLBACK_SHAPE_CLOSURE=FAIL mapping scope shrank: {all_mapping_count} < 106', file=sys.stderr); sys.exit(1)
if mismatches:
    print(f'W108_CALLBACK_SHAPE_CLOSURE=FAIL mismatches={len(mismatches)}', file=sys.stderr); sys.exit(1)
if not all(explicit.values()):
    print(f'W108_CALLBACK_SHAPE_CLOSURE=FAIL explicit_navigator_adapter={explicit}', file=sys.stderr); sys.exit(1)
print(f'W108_CALLBACK_SHAPE_CLOSURE=PASS mappings={all_mapping_count} callable_checked={len(rows)} mismatches=0')
