"""CPU checks only; synthetic vectors are not reported as Qwen results."""
import contextlib
import io
import json
import pathlib
import tempfile
import unittest
from unittest import mock

import numpy as np
import torch
import run


class DiagnosticTests(unittest.TestCase):
    def test_fixed_sample_and_baseline(self):
        rows = run.read_sample()
        self.assertEqual(len(rows), 63)
        baseline = [json.loads(x) for x in (run.HERE/'data/bleu_mapping.jsonl').read_text().splitlines()]
        self.assertEqual([x['question'] for x in rows], [x['question'] for x in baseline])
        self.assertEqual(len({x['bleu_cluster'] for x in baseline}), 22)

    def test_pool_padding_float32_and_normalization(self):
        h = torch.tensor([[[1.,0.],[0.,1.],[999.,999.]],[[100.,100.],[0.,2.],[0.,4.]]], dtype=torch.float16)
        m = torch.tensor([[1,1,0],[0,1,1]])
        out = run.masked_mean(h,m)
        expected = torch.tensor([[2**-.5,2**-.5],[0.,1.]])
        self.assertEqual(out.dtype,torch.float32)
        torch.testing.assert_close(out,expected)

    def test_pool_rejects_empty_zero_nan(self):
        for hidden,mask in [(torch.ones(1,2,2),torch.zeros(1,2)),(torch.zeros(1,2,2),torch.ones(1,2)),(torch.full((1,2,2),float('nan')),torch.ones(1,2))]:
            with self.assertRaises(ValueError):run.masked_mean(hidden,mask)

    def test_cosine_and_cluster_threshold(self):
        v = np.array([[1.,0.],[2.,0.],[0.,1.]])
        labels,dist = run.cluster(v,.5)
        self.assertEqual(labels,['E001','E001','E002'])
        np.testing.assert_allclose(dist,[[0,0,1],[0,0,1],[1,1,0]])
        self.assertEqual(len(set(run.cluster(v,1.1)[0])),1)

    def test_bad_vectors(self):
        for v in [np.zeros((3,2)),np.full((3,2),np.nan),np.ones((2,2))]:
            with self.assertRaises(ValueError):run.distance_matrix(v,3)

    def test_export_preserves_exact_questions(self):
        rows=run.read_sample()
        with tempfile.TemporaryDirectory() as t, contextlib.redirect_stdout(io.StringIO()):
            out=pathlib.Path(t)
            run.export(rows,['E001']*63,out,.5)
            mapping=[json.loads(x) for x in (out/'mapping.jsonl').read_text().splitlines()]
            self.assertEqual([x['question'] for x in mapping],[x['question'] for x in rows])
            text=(out/'clusters_original_questions.txt').read_text()
            for r in rows:self.assertIn(r['question'],text)
            self.assertEqual(json.loads((out/'summary.json').read_text())['K'],1)

    def test_main_and_verified_reuse(self):
        vectors=np.eye(63,dtype=np.float32)
        metadata=dict(identity=dict(model=run.MODEL,revision='synthetic-test-only'),pooling=run.POOLING)
        with tempfile.TemporaryDirectory() as t, contextlib.redirect_stdout(io.StringIO()):
            a,b,c=[pathlib.Path(t)/s for s in ['first','reuse','tampered']]
            with mock.patch.object(run,'embed',return_value=(vectors,metadata)):
                run.main(['--output',str(a)])
            with mock.patch.object(run,'embed',side_effect=AssertionError('must not load model')):
                run.main(['--output',str(b),'--reuse-embeddings',str(a),'--distance-threshold','1.1'])
            self.assertEqual(json.loads((a/'summary.json').read_text())['K'],63)
            self.assertEqual(json.loads((b/'summary.json').read_text())['K'],1)
            np.save(a/'embeddings.npy',np.ones((63,2)))
            with self.assertRaisesRegex(ValueError,'checksum'):
                run.main(['--output',str(c),'--reuse-embeddings',str(a)])

    def test_rejects_invalid_threshold(self):
        with contextlib.redirect_stderr(io.StringIO()):
            for value in ['0','nan','-1','2.1']:
                with self.assertRaises(SystemExit):run.main(['--output','unused','--distance-threshold',value])


if __name__=='__main__':unittest.main()
