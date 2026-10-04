import unittest
from interactive import run


class NavigationTests(unittest.TestCase):
    def simulate(self,commands):
        prompts=[];output=[];it=iter(commands)
        def read(prompt):
            prompts.append(prompt)
            try:return next(it)
            except StopIteration:raise EOFError
        self.assertEqual(run(read=read,write=output.append),0)
        return '\n'.join(prompts), '\n'.join(output)

    def test_quit_each_stage(self):
        for commands in [['q'],['1','q'],['C2v','q'],['C2v','','q'],['C2v','d','q'],['C2v','d','s','q']]:
            with self.subTest(commands=commands):self.assertIn('已退出',self.simulate(commands)[1])

    def test_back_each_stage(self):
        prompts,out=self.simulate(['1','0','C2v','0','C3v','','5','0','5','-1','1','0','home','q'])
        self.assertIn('Γ = A1 + 2E',out)
        self.assertGreaterEqual(prompts.count('[1/3]'),2)
        self.assertGreaterEqual(out.count('主菜单 ==='),3)

    def test_home_each_stage(self):
        for pre in [['1'],['C2v'],['C2v',''],['C2v','d'],['C2v','d','s']]:
            prompts,out=self.simulate(pre+['home','q'])
            self.assertEqual(out.count('主菜单 ==='),2)

    def test_numeric_zero(self):
        prompts,out=self.simulate(['C1','=0','q'])
        self.assertIn('Γ = 0',out)
        prompts,out=self.simulate(['C3v','','2','-1','=0','q'])
        self.assertIn('Γ = E',out)

    def test_errors_retry_and_export_cancel(self):
        prompts,out=self.simulate(['unknown','C2v','bad','d','s','0','q'])
        self.assertGreaterEqual(out.count('错误：'),2)
        self.assertEqual(out.count('Γ = 2A1 + A2 + B1 + B2'),2)


if __name__=='__main__':unittest.main()

