#!/usr/bin/env bash
# 使用明确固定的验证环境；任何缺失套件、解析失败或零测试都会失败。
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
if [ -n "${VERIFY_PYTHON:-}" ]; then
  PY="$VERIFY_PYTHON"
elif [ -x /tmp/[PRODUCT]_verify_venv/bin/python ]; then
  PY=/tmp/[PRODUCT]_verify_venv/bin/python
else
  PY=python3
fi
export SKILLS_DIR="$(cd "$SCRIPT_DIR/../../skills" && pwd)"
"$PY" - "$SCRIPT_DIR" <<'PYCODE'
import contextlib, importlib.util, importlib.metadata, io, json, pathlib, sys, traceback
root = pathlib.Path(sys.argv[1])
expected = {'[BASE-ADK]-python':'1.1.13','[PRODUCT]-sdk-python':'0.8.7','google-adk':'2.2.0'}
actual = {}
for package, version in expected.items():
    try:
        actual[package] = importlib.metadata.version(package)
    except importlib.metadata.PackageNotFoundError:
        raise SystemExit(f'缺少验证依赖 {package}；请用 VERIFY_PYTHON 指向安装了精确版本的 Python 环境。')
    if actual[package] != version:
        raise SystemExit(f'验证版本不匹配：{package}={actual[package]}，需要 {version}')
specs = [('test_imports','run_import_tests',25),('test_signatures','run_signature_tests',36),('test_code_blocks','run_code_block_tests',15),('test_session_semantics','run_session_semantics_tests',8)]
reports=[]
log=io.StringIO()
for name, function, expected_count in specs:
    try:
        with contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
            module_spec=importlib.util.spec_from_file_location(name,root/f'{name}.py')
            module=importlib.util.module_from_spec(module_spec)
            module_spec.loader.exec_module(module)
            report=getattr(module,function)()
        count=len(report.get('results',[]))
        passed=sum(item.get('passed') is True for item in report.get('results',[]))
        failed=count-passed
        if count != expected_count or report.get('passed') != passed or report.get('failed') != failed:
            raise ValueError(f'{name}: 测试数量或汇总不一致，实际{count}，期望{expected_count}')
        if name=='test_code_blocks' and report.get('skills_scanned')!=14:
            raise ValueError('未检查全部14个Skill')
        reports.append(report)
    except Exception:
        reports.append({'suite':name,'passed':0,'failed':1,'error':traceback.format_exc()})
summary={'environment':{'python':sys.version,'packages':actual},'overall_passed':sum(x['passed'] for x in reports),'overall_failed':sum(x['failed'] for x in reports),'suites':reports,'scope':'import/参数与默认值/语法/源码结构；不包含业务运行或云端调用'}
text=json.dumps(summary,ensure_ascii=False,indent=2)
(root/'results.json').write_text(text+'\n',encoding='utf-8')
(root/'test_log.txt').write_text(log.getvalue()+'\n'+text+'\n',encoding='utf-8')
print(json.dumps({'passed':summary['overall_passed'],'failed':summary['overall_failed'],'suites':len(reports),'versions':actual},ensure_ascii=False))
raise SystemExit(1 if summary['overall_failed'] or len(reports)!=len(specs) else 0)
PYCODE
