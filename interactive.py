"""Stateful CLI navigation. Control words are recognized before number parsing."""
import json
from pathlib import Path
from core import COMMON, get_table, number, parse_vector, payload, report

from i18n import tr, error_text, LANGUAGES
from preferences import save_language


def run(initial_group=None, read=input, write=print, language='zh-Hans'):
    def t(key, **values): return tr(key, language, **values)
    stage='group' if initial_group else 'home'
    table=None; values=[]; result=None
    pending=initial_group
    def ask(prompt):
        try:return read(prompt).strip()
        except (EOFError,KeyboardInterrupt):return 'q'
    while True:
        if stage=='home':
            write(t('cli_home'))
            s=ask(t('cli_choice'))
            if s.lower() == 'lang':
                selected = ask('en / zh-Hans / zh-Hant (0: Back, q: Exit): ')
                if selected == 'q': break
                if selected in LANGUAGES:
                    language = selected
                    save_language(language)
                continue
            if s.lower()=='q':break
            if s.lower() in ('0','home','h'):continue
            if s=='2':
                write(t('cli_scope')+', '.join(COMMON))
                continue
            stage='group';pending=None if s=='1' else s
            continue
        write(t('cli_nav'))
        if stage=='group':
            s=pending if pending is not None else ask(t('cli_group'))
            pending=None
        elif stage=='vector':
            write(report(table,language=language))
            s=ask(t('cli_vector'))
        elif stage=='items':
            j=len(values)
            s=ask(f'[{j+1}/{len(table.classes)}] χ({table.classes[j]}), n_j={table.sizes[j]}：')
        elif stage=='result':
            write(report(table,result,language=language))
            s=ask(t('cli_result'))
        else:
            s=ask(t('cli_path'))
        cmd=s.lower()
        if cmd == 'lang':
            selected = ask('en / zh-Hans / zh-Hant (0: Back, q: Exit): ')
            if selected == 'q': break
            if selected in LANGUAGES:
                language = selected
                save_language(language)
            continue
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
                c=table.orbital_exact(2) if cmd=='d' else parse_vector(s[1:] if s.startswith('=') else s)
                result=table.reduce(c);stage='result'
            elif stage=='items':
                values.append(number(s[1:] if s.startswith('=') else s))
                if len(values)==len(table.classes):result=table.reduce(values);stage='result'
            elif stage=='result':
                if cmd=='1':values=[];stage='vector'
                elif cmd=='2':stage='group'
                elif cmd=='s':stage='export'
                else:write(t('cli_choose'))
            elif stage=='export':
                if not s:raise ValueError(t('cli_empty_path'))
                p=Path(s).expanduser()
                if p.exists():
                    write(t('cli_existing'));continue
                p.write_text(json.dumps(payload(table,result),ensure_ascii=False,indent=2),encoding='utf-8')
                write(t('saved',path=str(p)));stage='result'
        except (ValueError,OSError) as e:write(t('cli_error',reason=error_text(e,language)))
    write(t('cli_exited'))
    return 0

