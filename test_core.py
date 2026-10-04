"""Run: python -m unittest -v. Tests include independent orbital transforms."""
import json
import os
import subprocess
import sys
import unittest
import numpy as np
from core import COMMON, matching_groups, get_table, number, parse_vector, payload


class CharacterTests(unittest.TestCase):
    def test_cli_redirected_legacy_encoding(self):
        env = dict(os.environ, PYTHONIOENCODING='ascii', PYTHONUTF8='0')
        result = subprocess.run([sys.executable, 'pointgroup.py', 'C2v', '--c', '5,1,1,1'],
                                env=env, capture_output=True, check=True)
        output = result.stdout.decode('utf-8')
        self.assertIn('2A1 + A2 + B1 + B2', output)
        self.assertIn('Γ', output)

    def test_families_and_round_trip(self):
        rng=np.random.default_rng(42)
        for name in COMMON:
            with self.subTest(group=name):
                t=get_table(name);self.assertLess(t.check(),1e-10)
                a=rng.integers(0,4,len(t.irreps));r=t.reduce(t.X.T@a)
                self.assertTrue(r['valid']);np.testing.assert_allclose(r['a'],a,atol=1e-10)
                # Every central shell l=0..4 must restrict to a valid representation.
                for l in range(5):self.assertTrue(t.reduce(t.orbital(l))['valid'])

    def test_expanded_catalogue_and_search(self):
        self.assertEqual(len(COMMON), 423)
        self.assertEqual(len(COMMON), len(set(COMMON)))
        for name in ('C9h', 'C12v', 'D30h', 'D60d', 'S120', 'Ih'):
            self.assertIn(name, COMMON)
        self.assertEqual(matching_groups('D_12'), ['D12', 'D12h', 'D12d'])
        self.assertEqual(matching_groups(' c_{60} '), ['C60', 'C60v', 'C60h'])
        self.assertEqual(matching_groups(''), COMMON)
        self.assertEqual(matching_groups('not-a-group'), [])
        # Manual entry beyond the visible catalogue stays available.
        self.assertEqual(get_table('C61v').name, 'C61v')

    def test_known_d_splittings(self):
        known={'C2v':{'A1':2,'A2':1,'B1':1,'B2':1},
               'C3v':{'A1':1,'E':2},'D4h':{'A1g':1,'B1g':1,'B2g':1,'Eg':1},
               'Oh':{'Eg':1,'T2g':1},'Td':{'E':1,'T2':1},'Ih':{'Hg':1},
               'D3h':{"A1'":1,"E'":1,"E''":1},'D3d':{'A1g':1,'Eg':2},
               'D2h':{'Ag':2,'B1g':1,'B2g':1,'B3g':1},
               'T':{'E+':1,'E-':1,'T':1}}
        for name,expected in known.items():
            t=get_table(name);r=t.reduce(t.orbital(2))
            self.assertEqual({x:int(a) for x,a in zip(t.irreps,r['integer_a']) if a},expected)

    def test_orbital_polynomial_independent(self):
        # Real traceless symmetric tensors span the five d orbitals.
        q=[]
        q += [np.diag([1,-1,0])/np.sqrt(2),np.diag([-1,-1,2])/np.sqrt(6)]
        for i,j in [(0,1),(0,2),(1,2)]:
            a=np.zeros((3,3));a[i,j]=a[j,i]=1/np.sqrt(2);q.append(a)
        for name in ('C7h','D4d','D5d','D6h','S8','C2v','Td','Oh','Ih'):
            t=get_table(name)
            chars=[sum(np.trace(A.T@M@A@M.T) for A in q) for M in t.reps]
            np.testing.assert_allclose(chars,t.orbital(2),atol=1e-12)

    def test_complex_conjugation(self):
        t=get_table('C3')
        r=t.reduce(t.X[1]);np.testing.assert_allclose(r['a'],[0,1,0],atol=1e-12)
        self.assertTrue(r['valid'])
        # Omitting conjugation swaps the two nontrivial irreps.
        self.assertFalse(np.allclose(t.X@(t.sizes*t.X[1])/t.h,r['a']))

    def test_class_weight(self):
        t=get_table('C3v');r=t.reduce([5,-1,1])
        np.testing.assert_allclose(r['a'],[1,0,2],atol=1e-12)

    def test_bad_input(self):
        t=get_table('C2v')
        self.assertFalse(t.reduce([5,0,0,0])['valid'])
        self.assertFalse(t.reduce([-1,-1,-1,-1])['valid'])
        for c in ([1,2], [float('nan'),0,0,0], [[1,1,1,1]]):
            with self.assertRaises(ValueError):t.reduce(c)
        for g in ['D1','C0','C3d','S4h','Cinfv','D∞h','madeup']:
            with self.assertRaises(ValueError):get_table(g)
        for expr in ['__import__("os")','1/0','float("nan")','x','sqrt(1,2)','1e999']:
            with self.assertRaises(ValueError):number(expr)
        for tol in (0,-1,float('nan'),1):
            with self.assertRaises(ValueError):t.reduce([1,1,1,1],tol)

    def test_parser_and_json(self):
        self.assertAlmostEqual(number('exp(2*pi*i/3)'),-.5+np.sqrt(3)*.5j)
        self.assertEqual(number('1+2i'),1+2j)
        self.assertAlmostEqual(number('(1+sqrt(5))/2'),(1+np.sqrt(5))/2)
        np.testing.assert_allclose(parse_vector('5, 1/2 + 1/2, 1, 1'),[5,1,1,1])
        t=get_table('C3');data=json.loads(json.dumps(payload(t,t.reduce(t.X[1]))))
        self.assertTrue(data['result']['valid']);self.assertIn('im',data['X'][1][1])

    def test_cli(self):
        for argv,code,fragment in [(['C2v','--c','5,1,1,1'],0,'2A1 + A2 + B1 + B2'),
                                    (['C3v','--c','5,0,0'],2,'不是容差内'),
                                    (['Cinfv','--table'],1,'Haar'),
                                    (['--list'],0,'S2n')]:
            p=subprocess.run([sys.executable,'pointgroup.py']+argv,text=True,capture_output=True)
            self.assertEqual(p.returncode,code,p.stderr);self.assertIn(fragment,p.stdout+p.stderr)
        p=subprocess.run([sys.executable,'pointgroup.py'],input='C2v\n5,1,1,1\n',text=True,capture_output=True)
        self.assertEqual(p.returncode,0,p.stderr);self.assertIn('2A1',p.stdout)


if __name__=='__main__':unittest.main()
