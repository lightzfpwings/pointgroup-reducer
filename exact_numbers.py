"""Exact display values, kept separate from floating-point reduction checks.

Expressions come only from our character formulas or the validated input AST;
user strings are never passed to SymPy's evaluating string parser.
"""
from functools import lru_cache
import ast
import re
import sympy as s


class ExactNumber(complex):
    def __new__(cls, value, expression):
        obj = super().__new__(cls, value)
        obj.expression = s.sympify(expression)
        return obj


def expression(value):
    if isinstance(value, s.Basic):
        return value
    if isinstance(value, ExactNumber):
        return value.expression
    z = complex(value)
    # Do not infer radicals from rounded decimal data.
    return s.Rational(str(z.real)) + s.I * s.Rational(str(z.imag))


def wrapped(expr):
    return ExactNumber(complex(expr.evalf()), expr)


@lru_cache(maxsize=8192)
def cos_pi(p, q):
    angle = s.Rational(p, q) % 2
    if angle > 1:
        angle = 2 - angle
    sign = 1
    if angle > s.Rational(1, 2):
        angle = 1 - angle
        sign = -1
    # Familiar radicals stay compact; general orders retain exact cosines.
    return sign * s.cos(s.pi * angle, evaluate=angle.q in (1, 2, 3, 4, 5, 6, 8, 10, 12))


def root_of_unity(p, n):
    return cos_pi(2*p, n) + s.I*cos_pi(n-4*p, 2*n)


def ast_expression(node, source):
    if isinstance(node, ast.Expression):
        return ast_expression(node.body, source)
    if isinstance(node, ast.Constant):
        if type(node.value) is int:
            return s.Integer(node.value)
        token = ast.get_source_segment(source, node).replace('_', '')
        return s.Rational(token[:-1])*s.I if token[-1:] in ('j', 'J') else s.Rational(token)
    if isinstance(node, ast.Name):
        return {'i': s.I, 'j': s.I, 'pi': s.pi, 'e': s.E}[node.id]
    if isinstance(node, ast.UnaryOp):
        value = ast_expression(node.operand, source)
        return -value if isinstance(node.op, ast.USub) else value
    if isinstance(node, ast.BinOp):
        a, b = ast_expression(node.left, source), ast_expression(node.right, source)
        if isinstance(node.op, ast.Add): return a+b
        if isinstance(node.op, ast.Sub): return a-b
        if isinstance(node.op, ast.Mult): return a*b
        if isinstance(node.op, ast.Div): return a/b
        # Numeric validation has already bounded the exponent.
        return s.Pow(a, b)
    arg = ast_expression(node.args[0], source)
    name = node.func.id
    if name in ('sin', 'cos') and (arg/s.pi).is_Rational:
        ratio = arg/s.pi
        if name == 'sin': ratio = s.Rational(1, 2)-ratio
        return cos_pi(int(ratio.p), int(ratio.q))
    if name == 'exp' and (arg/(s.pi*s.I)).is_Rational:
        ratio = arg/(s.pi*s.I)
        return root_of_unity(int(ratio.p), 2*int(ratio.q))
    return {'sqrt': s.sqrt, 'sin': s.sin, 'cos': s.cos, 'exp': s.exp}[name](arg)


def input_text(value):
    return str(expression(value)).replace('I', 'i').replace('E', 'e')


def plain(value):
    text = input_text(value).replace('pi', 'π')
    text = re.sub(r'sqrt\((\d+)\)', r'√\1', text)
    return text.replace('sqrt(', '√(').replace('**', '^')


def tex(value):
    return s.latex(expression(value), imaginary_unit='i', fold_short_frac=False)


def result_values(table, result, key):
    if key == 'c':
        return result.get('c_exact', result['c'])
    if key == 'a':
        if 'a_exact' not in result:
            c = [expression(z) for z in result_values(table, result, 'c')]
            values = [s.expand(s.Add(*(s.conjugate(table.symbolic(i,j))*int(w)*z
                                       for j,(w,z) in enumerate(zip(table.sizes,c))))/table.h)
                      for i in range(len(table.irreps))]
            # Never turn a near-integer input into an exact integer merely
            # because it passes the numerical tolerance used for validation.
            result['a_exact'] = [s.simplify(z) if s.count_ops(z) <= 80 else z for z in values]
        return result['a_exact']
    raise KeyError(key)
