#!/usr/bin/env python3
"""CLI entry point; use --gui for the desktop application."""
import argparse
import csv
import json
from pathlib import Path
import sys
from i18n import tr, error_text, LANGUAGES
from preferences import load_language
from core import COMMON, fmt, get_table, parse_vector, payload, report, number


def main(argv=None):
    # Frozen Windows executables may use the legacy code page for redirected
    # output despite PYTHONUTF8. Keep Chinese text and symmetry symbols intact.
    for stream in (sys.stdin, sys.stdout, sys.stderr):
        if stream is not None and hasattr(stream, 'reconfigure'):
            stream.reconfigure(encoding='utf-8')
    pre=argparse.ArgumentParser(add_help=False)
    pre.add_argument('--lang', choices=list(LANGUAGES))
    options,_=pre.parse_known_args(argv)
    language=options.lang or load_language()
    def t(key, **values): return tr(key,language,**values)
    p=argparse.ArgumentParser(description=t('cli_description'))
    p.add_argument('group',nargs='?',help=t('arg_group'))
    p.add_argument('--c',help=t('arg_c'))
    p.add_argument('--gui',action='store_true',help=t('arg_gui'))
    p.add_argument('--list',action='store_true',help=t('arg_list'))
    p.add_argument('--table',action='store_true',help=t('arg_table'))
    p.add_argument('--shell',type=int,metavar='L',help=t('arg_shell'))
    p.add_argument('--json',type=Path,help=t('arg_json'))
    p.add_argument('--csv',type=Path,help=t('arg_csv'))
    p.add_argument('--tol',type=float,default=1e-7,help=t('arg_tol'))
    p.add_argument('--lang', choices=list(LANGUAGES), help='Language / 语言 / 語言: en, zh-Hans, zh-Hant')
    args=p.parse_args(argv)
    language=args.lang or load_language()
    try:
        if args.gui:
            from gui import launch
            launch(args.group or 'C2v',language)
            return 0
        if args.list:
            print(tr('cli_scope',language)+', '.join(COMMON))
            print(tr('guide_scope',language))
            return 0
        if not args.table and args.c is None and args.shell is None:
            from interactive import run
            return run(args.group,language=language)
        if not args.group:
            raise ValueError(t('arg_missing_group'))
        t=get_table(args.group)
        if args.c is not None and args.shell is not None:
            raise ValueError(t('arg_conflict'))
        result=None
        if args.c is not None: result=t.reduce(parse_vector(args.c),args.tol)
        elif args.shell is not None: result=t.reduce(t.orbital(args.shell),args.tol)
        print(report(t,result,language=language))
        if args.json:
            args.json.write_text(json.dumps(payload(t,result),ensure_ascii=False,indent=2),encoding='utf-8')
            print(tr('saved',language,path=str(args.json)))
        if args.csv:
            with args.csv.open('w',encoding='utf-8-sig',newline='') as f:
                writer=csv.writer(f)
                writer.writerow(['irrep']+t.classes)
                writer.writerow(['n_j']+t.sizes.tolist())
                writer.writerows([[label]+[fmt(z,15) for z in row] for label,row in zip(t.irreps,t.X)])
            print(tr('saved',language,path=str(args.csv)))
        return 0 if result is None or result['valid'] else 2
    except (ValueError,OSError,EOFError,ImportError) as e:
        print(tr('cli_error',language,reason=error_text(e,language)),file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print(tr('cli_cancelled',language),file=sys.stderr)
        return 130


if __name__=='__main__':
    raise SystemExit(main())
