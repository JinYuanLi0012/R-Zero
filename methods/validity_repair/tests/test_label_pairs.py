import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import label_pairs as p


def sources(directory):
    audit=[]; orig=[]; rep=[]
    for key,status,q,new in [('a','unchanged_valid','shared','shared'),('b','accepted','old','new'),('c','unrepairable','drop','drop')]:
        audit.append(dict(id=key,status=status,source_validity='VALID' if key=='a' else 'INVALID',original_question=q,final_question=new))
        orig.append(dict(id=key,round='v1',split='train',question=q))
        rep.append(dict(id=key,round='v1',split='train',question=new))
    for name,data in [('repair_audit',audit),('original_questions',orig),('repaired_questions',rep)]:
        p.write_jsonl(directory/(name+'.jsonl'),data)


class Tests(unittest.TestCase):
    def test_vote_equivalence_ties_and_timeout(self):
        eq=lambda a,b: {a,b}=={'1/2','0.5'}
        v=p.majority_vote(['1/2','0.5','2',None],eq)
        self.assertEqual(v['answer'],'1/2');self.assertAlmostEqual(v['score'],2/3)
        self.assertEqual(p.majority_vote(['2','1'],eq)['answer'],'2')
        self.assertEqual(p.majority_vote(['x','y'],lambda a,b:'TIMED_OUT')['answer_counts'],{'x':1,'y':1})
        self.assertEqual(p.majority_vote(['no solution','no roots'],eq)['score'],1)
        self.assertFalse(p.usable('None'));self.assertFalse(p.usable('INVALID'))
        self.assertTrue(p.usable('no solution'))

    def test_pairwise_drop_and_shared_labels(self):
        with tempfile.TemporaryDirectory() as tmp:
            d=Path(tmp);sources(d)
            pairs,jobs,_=p.prepare(d,d/'out')
            self.assertEqual(len(pairs),2);self.assertEqual(len(jobs),3)
            artifacts={j['job_id']:{'job_id':j['job_id'],'status':'complete','answer':'7','score':1.0} for j in jobs}
            stats=p.finalize(pairs,artifacts,d/'out')
            self.assertEqual(stats['kept_pairs'],2)
            a=p.read_jsonl(d/'out/original_train.jsonl');b=p.read_jsonl(d/'out/repaired_train.jsonl')
            self.assertEqual(a[0],b[0]);self.assertEqual(a[1]['problem'],'old');self.assertEqual(b[1]['problem'],'new')
            artifacts[pairs[1]['repaired_job']]['status']='no_usable_answer'
            stats=p.finalize(pairs,artifacts,d/'out');self.assertEqual(stats['kept_pairs'],1)
            with self.assertRaises(ValueError):p.prepare(d,d/'out',1)

    def test_base_prompt_fallback(self):
        self.assertEqual(p.render_prompt(NS(chat_template=None),'test'),
                         'system: Please reason step by step, and put your final answer within \\boxed{}.\nuser: test')

    def test_cli_generation_resume_and_sampling_contract(self):
        with tempfile.TemporaryDirectory() as tmp:
            d=Path(tmp);sources(d);calls=[]
            class Tokenizer:
                chat_template=None;eos_token_id=2
                def encode(self,t):return list(range(len(t)))
            class LLM:
                def __init__(self,**kw):calls.append(('init',kw))
                def generate(self,prompts,sampling_params,use_tqdm):
                    calls.append(('generate',sampling_params))
                    return [NS(outputs=[NS(text='7',finish_reason='stop') for _ in range(s.n)]) for s in sampling_params]
            mods={'vllm':NS(LLM=LLM,SamplingParams=lambda **kw:NS(**kw)),
                  'transformers':NS(AutoTokenizer=NS(from_pretrained=lambda *a,**kw:Tokenizer())),
                  'stopit':NS(threading_timeoutable=lambda **kw:lambda f:lambda a,b,**kw:f(a,b)),
                  'mathruler':NS(), 'mathruler.grader':NS(extract_boxed_content=lambda t:t,grade_answer=lambda a,b:a==b)}
            argv=['label_pairs.py','--repair-dir',str(d),'--output-dir',str(d/'out')]
            with patch.dict(sys.modules,mods),patch.object(sys,'argv',argv):
                p.main();p.main()
            self.assertEqual(sum(c[0]=='init' for c in calls),1)
            samplings=[c[1] for c in calls if c[0]=='generate'][0]
            self.assertEqual(len(samplings),3)
            self.assertTrue(all((s.n,s.temperature,s.top_p,s.top_k,s.max_tokens)==(9,1.0,1.0,40,4096) for s in samplings))
            self.assertEqual(len(p.read_jsonl(d/'out/original_train.jsonl')),2)

if __name__=='__main__':unittest.main()
