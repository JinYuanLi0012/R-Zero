import json
from pathlib import Path
import tempfile
import unittest
from evaluation.supergpqa_shards import partition, merge_shards


class ShardTests(unittest.TestCase):
    def test_disjoint_complete_and_balanced_by_discipline(self):
        rows = [{'discipline': c, 'question': str(i)} for c, n in [('Science', 9), ('Engineering', 7), ('Law', 3)] for i in range(n)]
        categories = ['Engineering', 'Science', 'Law']
        a, n, digest = partition(rows, categories, 0, 2)
        b, m, other_digest = partition(rows, categories, 1, 2)
        self.assertEqual((n, digest), (m, other_digest))
        self.assertEqual(len(a) + len(b), len(rows))
        self.assertLessEqual(abs(len(a) - len(b)), 1)
        self.assertEqual(sorted(r['_evaluation_index'] for r in a + b), list(range(len(rows))))
        for category in categories:
            self.assertLessEqual(abs(sum(r['discipline'] == category for r in a) - sum(r['discipline'] == category for r in b)), 1)

    def test_merge_rejects_duplicate_or_mismatched_dataset(self):
        root = Path(tempfile.mkdtemp())
        folders = [root / str(i) for i in range(2)]
        for i, folder in enumerate(folders):
            folder.mkdir()
            (folder / 'supergpqa_score.json').write_text(json.dumps(dict(model='m', dataset='supergpqa',
                shard_index=i, num_shards=2, total=2, correct=1, expected_total=4, dataset_fingerprint='same')))
            (folder / 'supergpqa_outputs.json').write_text(json.dumps([{'_evaluation_index': i}, {'_evaluation_index': i}]))
        with self.assertRaisesRegex(ValueError, 'duplicated'):
            merge_shards(folders, 'm', root)
        for i, folder in enumerate(folders):
            (folder / 'supergpqa_outputs.json').write_text(json.dumps([{'_evaluation_index': i}, {'_evaluation_index': i+2}]))
        score = folders[1] / 'supergpqa_score.json'
        record = json.loads(score.read_text())
        record['dataset_fingerprint'] = 'different'
        score.write_text(json.dumps(record))
        with self.assertRaisesRegex(ValueError, 'dataset mismatch'):
            merge_shards(folders, 'm', root)
        self.assertFalse((root / 'supergpqa_score.json').exists())
