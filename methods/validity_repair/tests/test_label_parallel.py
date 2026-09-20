import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import label_parallel as p

class Tests(unittest.TestCase):
    def test_device_mapping_and_finalize(self):
        with tempfile.TemporaryDirectory() as tmp:
            children=[];commands=[]
            class Child:
                pid=123
                def __init__(self,cmd,**kw):children.append((cmd,kw))
                def poll(self):return 0
                def wait(self,timeout):return 0
            argv=['label_parallel.py','--output-dir',tmp,'--gpus','2,4,6,7','--model','base']
            with patch.object(sys,'argv',argv),patch.object(p.subprocess,'Popen',Child),patch.object(p.subprocess,'run',lambda cmd,**kw:commands.append(cmd)):
                p.main()
            self.assertEqual([kw['env']['CUDA_VISIBLE_DEVICES'] for cmd,kw in children],['2','4','6','7'])
            self.assertEqual(len(children),4)
            self.assertTrue(commands[0][-1]=='--prepare-only' and commands[-1][-1]=='--finalize-only')
    def test_invalid_devices(self):
        for value in ('','0,0','0,','-1'):
            with self.assertRaises(ValueError):p.gpu_ids(value)
