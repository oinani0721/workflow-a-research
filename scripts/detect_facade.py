#!/usr/bin/env python3
import ast, os, sys
class FacadeDetector(ast.NodeVisitor):
    def __init__(self):
        self.warnings = []
    def visit_FunctionDef(self, node):
        if node.name.startswith('test_'):
            self.generic_visit(node); return
        body = [n for n in node.body if not (isinstance(n, ast.Expr) and isinstance(n.value, ast.Constant))]
        if len(body) > 2:
            self.warnings.append(f"FACADE: '{node.name}' line {node.lineno}, {len(body)} stmts")
        self.generic_visit(node)
if __name__ == "__main__":
    warnings = []
    for d in ["tests", "backend/tests"]:
        if not os.path.exists(d): continue
        for r, _, fs in os.walk(d):
            for f in fs:
                if f.startswith('test_') and f.endswith('.py'):
                    p = os.path.join(r, f)
                    try:
                        det = FacadeDetector(); det.visit(ast.parse(open(p).read()))
                        warnings.extend(f"{p}: {w}" for w in det.warnings)
                    except: pass
    for w in warnings: print(w, file=sys.stderr)
    sys.exit(2 if warnings else 0)
