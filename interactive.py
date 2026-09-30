"""Stateful CLI navigation. Control words are recognized before number parsing."""
import json
from pathlib import Path
from core import COMMON, get_table, number, parse_vector, payload, report


def run(initial_group=None, read=input, write=print):
    stage='group' if initial_group else 'home'
    table=None; values=[]; result=None
    pending=initial_group
    def ask(prompt):
        try:return read(prompt).strip()
        except (EOFError,KeyboardInterrupt):return 'q'
    while True:
        if stage=='home':
            write('\n=== 点群约化 · 主菜单 ===\n1 开始计算    2 支持范围    q 退出\n也可直接输入点群名，例如 C2v。')
            s=ask('选择：')
            if s.lower()=='q':break
            if s.lower() in ('0','home','h'):continue
            if s=='2':
                write('支持 Cn/Cnv/Cnh、Dn/Dnh/Dnd、S2n、T/Th/Td/O/Oh/I/Ih；无限群不适用。\n常用：'+', '.join(COMMON))
                continue
            stage='group';pending=None if s=='1' else s
            continue
        write('\n导航：0 上一步 | home 主菜单 | q 退出；数值零请写 =0（逗号向量中的 0 可直接写）。')
        if stage=='group':
            s=pending if pending is not None else ask('输入点群：')
            pending=None
        elif stage=='vector':
            write(report(table))
            s=ask('输入 c（逗号分隔；Enter 逐项输入；d 填入五个 d 轨道示例）：')
        elif stage=='items':
            j=len(values)
            s=ask(f'[{j+1}/{len(table.classes)}] χ({table.classes[j]}), n_j={table.sizes[j]}：')
        elif stage=='result':
            write(report(table,result))
            s=ask('1 重新输入 c | 2 更换点群 | s 导出 JSON | 0 返回输入 | home 主菜单 | q 退出：')
        else:
            s=ask('导出 JSON 路径（0 返回结果）：')
        cmd=s.lower()
        if cmd=='q':break
        if cmd in ('home','h'):
            table=None;values=[];result=None;stage='home';continue
        if cmd=='0':
            if stage=='group':stage='home'
            elif stage=='vector':stage='group'
            elif stage=='items':
                if values:values.pop()
                else:stage='vector'
            elif stage=='result':stage='vector'
            else:stage='result'
            continue
        try:
            if stage=='group':
                table=get_table(s);values=[];result=None;stage='vector'
            elif stage=='vector':
                if not s:values=[];stage='items';continue
                c=table.orbital(2) if cmd=='d' else parse_vector(s[1:] if s.startswith('=') else s)
                result=table.reduce(c);stage='result'
            elif stage=='items':
                values.append(number(s[1:] if s.startswith('=') else s))
                if len(values)==len(table.classes):result=table.reduce(values);stage='result'
            elif stage=='result':
                if cmd=='1':values=[];stage='vector'
                elif cmd=='2':stage='group'
                elif cmd=='s':stage='export'
                else:write('请选择 1、2、s、0、home 或 q。')
            elif stage=='export':
                if not s:raise ValueError('路径不能为空。')
                p=Path(s).expanduser()
                if p.exists():
                    write('该文件已存在，请换一个文件名，避免覆盖。');continue
                p.write_text(json.dumps(payload(table,result),ensure_ascii=False,indent=2),encoding='utf-8')
                write('已导出：'+str(p));stage='result'
        except (ValueError,OSError) as e:write('错误：'+str(e)+'；可以重试或使用导航命令。')
    write('已退出。')
    return 0
