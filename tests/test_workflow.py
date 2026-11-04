import tempfile, unittest
from pathlib import Path
from autodesign import Workflow
class WorkflowTests(unittest.TestCase):
 def test_review_integration_rollback(self):
  with tempfile.TemporaryDirectory() as t:
   w=Workflow(t); p=Path(t);(p/'index.html').write_text('old.jpg');(p/'assets/pending').mkdir(parents=True);(p/'assets/pending/a.jpg').write_bytes(b'image')
   w.data['assets']=[dict(id='a',path='assets/pending/a.jpg',status='pending')]
   b=[dict(file='index.html',old='old.jpg',asset='a')]
   with self.assertRaises(ValueError):w.integrate(b)
   w.decide('a','approved');w.integrate(b)
   self.assertIn('assets/approved/a.jpg',(p/'index.html').read_text());w.rollback();self.assertEqual((p/'index.html').read_text(),'old.jpg')
 def test_path_escape(self):
  with tempfile.TemporaryDirectory() as t:
   with self.assertRaises(ValueError):Workflow(t).safe('../outside')
 def test_rollback_preserves_edits(self):
  with tempfile.TemporaryDirectory() as t:
   w=Workflow(t);p=Path(t);(p/'i.html').write_text('old');w.data['assets']=[dict(id='a',path='assets/a.jpg',status='approved')];w.integrate([dict(file='i.html',old='old',asset='a')]);(p/'i.html').write_text('user edit')
   with self.assertRaises(ValueError):w.rollback()
   self.assertEqual((p/'i.html').read_text(),'user edit')
