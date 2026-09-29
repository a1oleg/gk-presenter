import sys, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from render_independent_scenes import fit_code, code_frame

FONT=Path('C:/Windows/Fonts/consola.ttf')

@unittest.skipUnless(FONT.exists(),'Windows Consolas fixture is unavailable')
class CodeLayoutTests(unittest.TestCase):
    def snapshot(self,text):
        return {'code':text,'colors':['#ffffff']*(len(text.encode('utf-16-le'))//2),'lineMap':list(range(1,len(text.split('\n'))+1))}

    def test_complete_source_fits_independent_track(self):
        snapshot=self.snapshot('const value = 1;\nreturn value;')
        layout=fit_code(snapshot,(800,400),str(FONT))
        self.assertEqual(code_frame(snapshot,layout,(800,400)).size,(800,400))
        self.assertGreaterEqual(layout['fontSize'],18)

    def test_long_line_is_rejected_instead_of_cropped(self):
        with self.assertRaisesRegex(ValueError,'does not fit'):
            fit_code(self.snapshot('x'*500),(800,400),str(FONT))

    def test_tall_source_is_rejected_instead_of_cropped(self):
        with self.assertRaisesRegex(ValueError,'does not fit'):
            fit_code(self.snapshot('\n'.join(['line']*100)),(800,400),str(FONT))

    def test_stale_color_map_is_rejected(self):
        snapshot=self.snapshot('text');snapshot['colors'].pop()
        with self.assertRaisesRegex(ValueError,'color map'):
            fit_code(snapshot,(800,400),str(FONT))

if __name__=='__main__':unittest.main()
