#!/usr/bin/env python3
"""CLI entry point; use --gui for the desktop application."""
import argparse
import csv
import json
from pathlib import Path
import sys
from core import COMMON, fmt, get_table, parse_vector, payload, report, number


def main(argv=None):
    p=argparse.ArgumentParser(description='点群特征标约化：a = X.conj() @ W @ c / h')
    p.add_argument('group',nargs='?',help='例如 C2v、D4h、Ih 或 C17v')
    p.add_argument('--c',help='按列输入，用逗号分隔，例如 --c "5,1,1,1"')
    p.add_argument('--gui',action='store_true',help='打开 Tkinter 图形界面')
    p.add_argument('--list',action='store_true',help='显示点群覆盖范围')
    p.add_argument('--table',action='store_true',help='仅查看特征标表')
    p.add_argument('--shell',type=int,metavar='L',help='中心原子轨道示例：s=0、p=1、d=2、f=3')
    p.add_argument('--json',type=Path,help='导出完整表与结果 JSON')
    p.add_argument('--csv',type=Path,help='导出特征标表 CSV')
    p.add_argument('--tol',type=float,default=1e-7,help='绝对容差，默认 1e-7')
    args=p.parse_args(argv)
    try:
        if args.gui:
            from gui import launch
            launch(args.group or 'C2v')
            return 0
        if args.list:
            print('有限单值点群：C1, Cs, Ci; Cn, Cnv, Cnh; Dn, Dnh, Dnd; S2n; T, Th, Td, O, Oh, I, Ih')
            print('n 为正整数，Dn 系列 n≥2；稠密矩阵实现上限 n=2000。奇数 Sn 作为 Cnh 的别名。')
            print('无限点群 C∞v、D∞h 不适用有限 h、X、W 公式；不包含双群/磁群/空间群。')
            print('常用选择：'+', '.join(COMMON))
            return 0
        if not args.table and args.c is None and args.shell is None:
            from interactive import run
            return run(args.group)
        if not args.group:
            raise ValueError('非交互模式请指定点群，例如 C2v --table；交互菜单请直接运行程序。')
        t=get_table(args.group)
        if args.c is not None and args.shell is not None:
            raise ValueError('--c 与 --shell 只能选择一个。')
        result=None
        if args.c is not None: result=t.reduce(parse_vector(args.c),args.tol)
        elif args.shell is not None: result=t.reduce(t.orbital(args.shell),args.tol)
        print(report(t,result))
        if args.json:
            args.json.write_text(json.dumps(payload(t,result),ensure_ascii=False,indent=2),encoding='utf-8')
            print(f'已导出：{args.json}')
        if args.csv:
            with args.csv.open('w',encoding='utf-8-sig',newline='') as f:
                writer=csv.writer(f)
                writer.writerow(['irrep']+t.classes)
                writer.writerow(['n_j']+t.sizes.tolist())
                writer.writerows([[label]+[fmt(z,15) for z in row] for label,row in zip(t.irreps,t.X)])
            print(f'已导出：{args.csv}')
        return 0 if result is None or result['valid'] else 2
    except (ValueError,OSError,EOFError,ImportError) as e:
        print(f'错误：{e}',file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print('\n已取消。',file=sys.stderr)
        return 130


if __name__=='__main__':
    raise SystemExit(main())
