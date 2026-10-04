"""Complete complex character tables for finite, single-valued 3D point groups.

X rows = irreps; columns = actual conjugacy classes. No real-row merging.
Analytic cyclic/dihedral families; explicit polyhedral tables; central products.
"""
from dataclasses import dataclass
from functools import lru_cache
from fractions import Fraction
from exact_numbers import ExactNumber, ast_expression, expression, cos_pi, root_of_unity, plain, result_values
import sympy as sp
import ast
import cmath
import math
import re
import numpy as np


def fmt(z, digits=8):
    return plain(z)


def number(text):
    """Small arithmetic grammar, deliberately not eval()."""
    text = text.strip().replace('−', '-').replace('^', '**').replace('π', 'pi')
    text = re.sub(r'√(\d+)', r'sqrt(\1)', text).replace('√(', 'sqrt(')
    text = re.sub(r'(?<=[0-9.)])i\b', '*i', text)
    if len(text) > 256:
        raise ValueError('数值表达式过长。')
    try:
        tree = ast.parse(text, mode='eval')
        if len(list(ast.walk(tree))) > 80:
            raise ValueError('表达式过于复杂。')
        def run(t):
            if isinstance(t, ast.Expression): return run(t.body)
            if isinstance(t, ast.Constant) and type(t.value) in (int, float, complex):
                return complex(t.value)
            if isinstance(t, ast.Name) and t.id in ('i', 'j', 'pi', 'e'):
                return {'i': 1j, 'j': 1j, 'pi': math.pi, 'e': math.e}[t.id]
            if isinstance(t, ast.UnaryOp) and isinstance(t.op, (ast.UAdd, ast.USub)):
                return run(t.operand) * (-1 if isinstance(t.op, ast.USub) else 1)
            if isinstance(t, ast.BinOp):
                a, b = run(t.left), run(t.right)
                if isinstance(t.op, ast.Add): return a+b
                if isinstance(t.op, ast.Sub): return a-b
                if isinstance(t.op, ast.Mult): return a*b
                if isinstance(t.op, ast.Div): return a/b
                if isinstance(t.op, ast.Pow) and abs(b) <= 100: return a**b
            if isinstance(t, ast.Call) and isinstance(t.func, ast.Name) and len(t.args)==1 and not t.keywords:
                fs = {'sqrt': cmath.sqrt, 'exp': cmath.exp, 'cos': cmath.cos, 'sin': cmath.sin}
                if t.func.id in fs: return fs[t.func.id](run(t.args[0]))
            raise ValueError('只支持数值、i、pi、四则运算、幂及 sqrt/exp/cos/sin。')
        z = complex(run(tree))
        if not (math.isfinite(z.real) and math.isfinite(z.imag)):
            raise ValueError('不能输入 NaN 或无穷大。')
        return ExactNumber(z, ast_expression(tree, text))
    except (SyntaxError, ZeroDivisionError, OverflowError, RecursionError) as e:
        raise ValueError('无效的数值表达式。') from e


def parse_vector(text):
    # Commas or semicolons allow spaces INSIDE each expression.
    parts = re.split(r'[,;，；]', text) if re.search(r'[,;，；]', text) else text.split()
    return [number(p) for p in parts]


def rz(t):
    c, s = math.cos(t), math.sin(t)
    return np.array([[c,-s,0],[s,c,0],[0,0,1.]])


@dataclass
class Table:
    name: str
    classes: list
    sizes: np.ndarray
    irreps: list
    X: np.ndarray
    reps: np.ndarray
    note: str = ''
    exact_entry: object = None

    def symbolic(self, i, j):
        return self.exact_entry(i, j) if self.exact_entry else expression(self.X[i,j])

    def symbolic_rows(self):
        return [[self.symbolic(i,j) for j in range(len(self.classes))]
                for i in range(len(self.irreps))]

    def orbital_exact(self, l=2):
        values = self.orbital(l)
        result = []
        for value, matrix in zip(values, self.reps):
            parity = 1 if np.linalg.det(matrix)>0 else -1
            theta = math.acos(float(np.clip((np.trace(parity*matrix)-1)/2, -1, 1)))
            # A finite-group operation has finite order dividing 2h after
            # removing inversion. Recover that rational angle, not a radical
            # guessed from the final floating-point character.
            turn = Fraction(theta/(2*math.pi)).limit_denominator(2*self.h)
            assert abs(float(turn)*2*math.pi-theta) < 1e-7
            expr = parity**l*(1+2*sum(cos_pi(2*m*turn.numerator, turn.denominator)
                                     for m in range(1,l+1)))
            result.append(ExactNumber(value, expr))
        return result

    @property
    def h(self): return int(sum(self.sizes))

    @property
    def W(self): return np.diag(self.sizes)

    def check(self):
        k = len(self.classes)
        if self.X.shape != (k,k) or len(self.irreps) != k:
            raise ValueError('特征标表必须为完整的方阵。')
        gram = (self.X.conj()*self.sizes) @ self.X.T / self.h
        error = float(np.max(np.abs(gram-np.eye(k))))
        if error > 1e-8:
            raise ValueError(f'特征标正交性校验失败：{error:g}')
        if not np.isclose(np.sum(self.X[:,0]**2), self.h):
            raise ValueError('不可约表示维数平方和不等于 h。')
        return error

    def orbital(self, l=2):
        """Characters of one central atomic shell; inversion parity (-1)^l."""
        if l < 0 or int(l) != l: raise ValueError('l 必须为非负整数。')
        result = []
        for M in self.reps:
            parity = 1 if np.linalg.det(M)>0 else -1
            proper = parity*M
            theta = math.acos(float(np.clip((np.trace(proper)-1)/2, -1, 1)))
            result.append(parity**l*(1+2*sum(math.cos(m*theta) for m in range(1,l+1))))
        return np.array(result, dtype=complex)

    def reduce(self, c, tol=1e-7):
        if not math.isfinite(tol) or not 0 < tol < .01:
            raise ValueError('容差必须大于 0 且小于 0.01。')
        originals = c
        c = np.asarray(c, dtype=complex)
        if c.shape != (len(self.classes),):
            raise ValueError(f'需要 {len(self.classes)} 个特征标，每个共轭类输入一个。')
        if not np.all(np.isfinite(c)): raise ValueError('输入必须是有限数。')
        a = self.X.conj() @ (self.sizes*c) / self.h
        nearest = np.rint(a.real)
        integral = bool(np.all(np.abs(a-nearest) <= tol) and np.all(nearest>=0))
        recovered = self.X.T @ a
        residual = float(np.max(np.abs(recovered-c)))
        int_residual = float(np.max(np.abs(self.X.T @ nearest-c)))
        valid = integral and int_residual <= tol
        return {'c': c, 'c_exact': [expression(z) for z in originals], 'a': a, 'integer_a': nearest.astype(object) if valid else None,
                'valid': valid, 'reconstructed_c': recovered, 'residual': residual,
                'integer_residual': int_residual,
                'dimension': c[0], 'tolerance': tol}

    def decomposition(self, result):
        if not result['valid']: return '输入不是容差内的合法表示特征标（重数须为非负整数）。'
        terms = []
        for name, a in zip(self.irreps, result['integer_a']):
            n = int(a)
            if n: terms.append(name if n==1 else f'{n}{name}')
        return 'Γ = ' + (' + '.join(terms) if terms else '0')


def make(name, classes, sizes, names, X, reps, note='', exact_entry=None):
    t = Table(name, classes, np.array(sizes, int), names,
              np.array(X, complex), np.array(reps, float), note, exact_entry)
    t.check()
    return t


def cyclic(n, name, generator, symbol):
    powers = list(range(n))
    order = [0] + ([n//2] if n%2==0 else [])
    for k in range(1, (n+1)//2): order += [k,n-k]
    labels = []
    for k in order:
        if symbol.startswith('S'): labels.append(f'R{k}')
        elif k==0: labels.append('A')
        elif 2*k==n: labels.append('B')
        else: labels.append(f'E{min(k,n-k)}'+('+' if k<n/2 else '-'))
    return make(name, ['E']+[symbol if p==1 else f'{symbol}^{p}' for p in powers[1:]],
                [1]*n, labels,
                [[cmath.exp(2j*math.pi*k*p/n) for p in powers] for k in order],
                [np.linalg.matrix_power(generator,p) for p in powers],
                f'生成元 r={symbol}；E_k+ / E_k- 为一维复共轭表示。'
                if not symbol.startswith('S') else
                f'Rk(r^p)=exp(2πikp/{n})，r={symbol}；Rk 是明确的生成元标签。',
                exact_entry=lambda i,j: root_of_unity(order[i]*j,n))


def dihedral(n, name, r, s, rsym, ssym, vertical=False):
    rotations = list(range(n//2+1))
    classes = ['E']+[rsym if p==1 else f'{rsym}^{p}' for p in rotations[1:]]
    sizes = [1]+[1 if 2*p==n else 2 for p in rotations[1:]]
    jlist = [0,1] if n%2==0 else [0]
    classes += [ssym if j==0 else f'{rsym}·{ssym}' for j in jlist]
    sizes += [n//2,n//2] if n%2==0 else [n]
    reps = [np.linalg.matrix_power(r,p) for p in rotations]
    reps += [np.linalg.matrix_power(r,j)@s for j in jlist]
    labels, rows = [], []
    for a,b,label in [(1,1,'A1'),(1,-1,'A2')]+([(-1,1,'B1'),(-1,-1,'B2')] if n%2==0 else []):
        labels.append(label)
        rows.append([a**p for p in rotations]+[a**j*b for j in jlist])
    for k in range(1,(n+1)//2):
        labels.append('E' if n in (3,4) else f'E{k}')
        rows.append([2*math.cos(2*math.pi*k*p/n) for p in rotations]+[0]*len(jlist))
    if n==2 and not vertical:
        labels = ['A','B1','B3','B2']
        indices = [0,1,3,2]
        rows = [rows[i] for i in indices]
        labels = [labels[i] for i in indices]
    return make(name, classes, sizes, labels, rows, reps,
                f'主轴 z；r={rsym}，s={ssym}；列为共轭类代表操作，n_j 单列显示。',
                exact_entry=lambda i,j: (2*cos_pi(2*(i-(4 if n%2==0 else 2)+1)*rotations[j],n)
                    if i >= (4 if n%2==0 else 2) and j < len(rotations) else sp.Integer(round(rows[i][j]))))


def product(base, name, central, symbol, suffixes):
    X = base.X
    return make(name, base.classes+[symbol if c=='E' else f'{symbol}·({c})' for c in base.classes],
                list(base.sizes)*2, [a+suffix for suffix in suffixes for a in base.irreps],
                np.block([[X,X],[X,-X]]),
                list(base.reps)+[central@m for m in base.reps],
                base.note+f' 后半列为 {symbol} 乘以前半列；后缀 {suffixes[0]}/{suffixes[1]} 表示对 {symbol} 的 ± 宇称。',
                exact_entry=lambda i,j: (-1 if i>=len(X) and j>=len(X) else 1)*base.symbolic(i%len(X),j%len(X)))


def polyhedral(name):
    if name in ('T','Th'):
        w=cmath.exp(2j*math.pi/3)
        b=make('T',['E','C3(+)','C3(-)','C2'],[1,4,4,3],['A','E+','E-','T'],
               [[1,1,1,1],[1,w,w.conjugate(),1],[1,w.conjugate(),w,1],[3,0,0,-1]],
               [np.eye(3),rz(2*math.pi/3),rz(-2*math.pi/3),rz(math.pi)],
               '两类 C3 分开；E+、E- 各为一维，化学实表示 E 是二者的直和。')
    elif name in ('O','Oh','Td'):
        # Column order E, C3, C2(coordinate), C4/S4, C2(edge)/sigma_d.
        td=name=='Td'
        b=make('Td' if td else 'O', ['E','C3','C2','S4' if td else 'C4','sigma_d' if td else "C2(edge)"],
               [1,8,3,6,6], ['A1','A2','E','T1','T2'],
               [[1,1,1,1,1],[1,1,1,-1,-1],[2,-1,2,0,0],[3,0,-1,1,-1],[3,0,-1,-1,1]],
               [np.eye(3),rz(2*math.pi/3),rz(math.pi),
                rz(math.pi/2)@np.diag([1,1,-1]) if td else rz(math.pi/2),
                np.diag([1,1,-1]) if td else rz(math.pi)])
    else:
        p=(1+math.sqrt(5))/2; q=1-p
        b=make('I',['E','C5','C5^2','C3','C2'],[1,12,12,20,15],['A','T1','T2','G','H'],
               [[1,1,1,1,1],[3,p,q,0,-1],[3,q,p,0,-1],[4,-1,-1,1,0],[5,0,0,-1,1]],
               [np.eye(3),rz(2*math.pi/5),rz(4*math.pi/5),rz(2*math.pi/3),rz(math.pi)])
    if name in ('T','Th'):
        b.exact_entry = lambda i,j: (root_of_unity((1 if i==1 else -1)*(1 if j==1 else -1),3)
                                     if i in (1,2) and j in (1,2) else sp.Integer(round(b.X[i,j].real)))
    elif name in ('I','Ih'):
        phi = (1+sp.sqrt(5))/2
        b.exact_entry = lambda i,j: (phi if i==j else 1-phi) if i in (1,2) and j in (1,2) else sp.Integer(round(b.X[i,j].real))
    # For polyhedra, reps encode only angle/parity (sufficient for central shells),
    # and are not one common spatial realization of the whole group.
    b.note += ' 多面体群的内部代表矩阵仅编码转角/宇称，供中心原子轨道示例使用。'
    return product(b,name,-np.eye(3),'i',('g','u')) if name.endswith('h') else b


def _build_table(raw):
    name = re.sub(r'[\s_{}]', '', raw).lower().replace('∞','inf')
    if name in ('cinfv','dinfh','c∞v','d∞h','cinfinityv','dinfinityh','kh','so3','o3'):
        raise ValueError('这是无限群，h 不是有限数，不能使用有限的 X、W 和 c。需以连续特征标函数及 Haar 积分约化；本程序的有限群模式不适用。')
    eye=np.eye(3); sh=np.diag([1,1,-1]); sv=np.diag([1,-1,1]); c2x=np.diag([1,-1,-1])
    if name=='c1': return make('C1',['E'],[1],['A'],[[1]],[eye])
    if name in ('cs','c1h','s1','c1v'):
        return make('Cs',['E','sigma_h'],[1,1],["A'","A''"],[[1,1],[1,-1]],[eye,sh])
    if name in ('ci','s2'):
        return make('Ci',['E','i'],[1,1],['Ag','Au'],[[1,1],[1,-1]],[eye,-eye])
    if name in ('t','th','td','o','oh','i','ih'):
        return polyhedral(name[0].upper()+name[1:])
    m=re.fullmatch(r'([cds])([1-9][0-9]*)([vhd]?)',name)
    if not m: raise ValueError('未知点群。支持 Cn、Cnv、Cnh、Dn、Dnh、Dnd、S2n、T/Th/Td/O/Oh/I/Ih。')
    family,ns,suffix=m.groups(); n=int(ns)
    if n>2000: raise ValueError('此实现为稠密矩阵，单次 n 上限为 2000；不是数学上的点群限制。')
    canonical=family.upper()+str(n)+suffix
    if family=='s' and not suffix:
        if n%2: return get_table(f'C{n}h')
        return cyclic(n,canonical,rz(2*math.pi/n)@sh,f'S{n}')
    if family=='c':
        if suffix=='': return cyclic(n,canonical,rz(2*math.pi/n),f'C{n}')
        if suffix=='v': return dihedral(n,canonical,rz(2*math.pi/n),sv,f'C{n}','sigma_v(xz)',True)
        if suffix=='h':
            b=get_table(f'C{n}')
            return product(b,canonical,-eye if n%2==0 else sh,'i' if n%2==0 else 'sigma_h',('g','u') if n%2==0 else ("'","''"))
    if family=='d' and n>=2:
        if suffix=='': return dihedral(n,canonical,rz(2*math.pi/n),c2x,f'C{n}',"C2'(x)")
        if suffix=='h':
            return product(get_table(f'D{n}'),canonical,-eye if n%2==0 else sh,'i' if n%2==0 else 'sigma_h',('g','u') if n%2==0 else ("'","''"))
        if suffix=='d':
            if n%2: return product(get_table(f'D{n}'),canonical,-eye,'i',('g','u'))
            return dihedral(2*n,canonical,rz(math.pi/n)@sh,c2x,f'S{2*n}',"C2'(x)")
    raise ValueError('该点群名称无效；Dn 系列要求 n≥2，S 系列不带后缀。')


@lru_cache(maxsize=64)
def get_table(raw):
    from operation_labels import direct_labels
    table = _build_table(raw)
    table.classes = direct_labels(table)
    return table


COMMON = ['C1','Cs','Ci','C2','C3','C4','C5','C6','C2v','C3v','C4v','C5v','C6v',
          'C2h','C3h','C4h','C6h','D2','D3','D4','D5','D6','D2h','D3h','D4h','D5h','D6h',
          'D2d','D3d','D4d','D5d','D6d','S4','S6','S8','T','Th','Td','O','Oh','I','Ih']


def report(table, result=None, language='zh-Hans'):
    from i18n import tr, group_notes
    def t(key, **values): return tr(key, language, **values)
    headers=['irrep']+table.classes
    rows=[headers,['n_j']+[str(n) for n in table.sizes]]
    rows += [[label]+[fmt(z) for z in row] for label,row in zip(table.irreps,table.symbolic_rows())]
    widths=[max(len(row[j]) for row in rows) for j in range(len(headers))]
    lines=[f'{table.name}    h = {table.h}',group_notes(table,language),t('cli_table_note')]
    lines += ['  '.join(s.rjust(w) for s,w in zip(row,widths)) for row in rows]
    lines += [t('cli_orthogonality',value=f'{table.check():.3g}'), 'a = (1/h) X.conj() @ W @ c']
    if result is not None:
        lines += ['c = ['+', '.join(fmt(z) for z in result_values(table, result, 'c'))+']',
                  'a = ['+', '.join(fmt(z) for z in result_values(table, result, 'a'))+']',
                  table.decomposition(result) if result['valid'] else t('representation_invalid'),
                  t('dimension')+f" = {fmt(result_values(table, result, 'c')[0])}; "+t('residual',value=f"{result['residual']:.3g}")]
    return '\n'.join(lines)


def payload(table, result=None):
    def encode(x):
        z=complex(x)
        return float(z.real) if abs(z.imag)<1e-12 else {'re':float(z.real),'im':float(z.imag)}
    data={'schema_version':1,'point_group':table.name,'h':table.h,'classes':table.classes,
          'class_sizes':table.sizes.tolist(),'W':table.W.tolist(),'irreps':table.irreps,
          'X':[[encode(x) for x in row] for row in table.X], 'note':table.note,
          'X_symbolic':[[plain(x) for x in row] for row in table.symbolic_rows()],
          'formula':'a = X.conj() @ W @ c / h','orthogonality_error':table.check()}
    if result is not None:
        data['result']={k: [encode(x) for x in result[k]] for k in ('c','a','reconstructed_c')}
        data['result']['symbolic'] = {key: [plain(x) for x in result_values(table,result,key)] for key in ('c','a')}
        data['result'].update(valid=result['valid'],residual=result['residual'],
                              integer_residual=result['integer_residual'],tolerance=result['tolerance'],
                              decomposition=table.decomposition(result))
    return data
