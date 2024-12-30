# Adapted from Tevatron (https://github.com/texttron/tevatron)

import os
import random
from argparse import ArgumentParser
from datetime import datetime
from multiprocessing import Pool

from tqdm import tqdm
from transformers import AutoTokenizer

from openmatch.utils import SimpleTrainPreProcessor as TrainPreProcessor


def load_ranking(rank_file, relevance, n_sample, depth):
    with open(rank_file) as rf:
        lines = iter(rf)
        q_0, _, p_0, _, _, _ = next(lines).strip().split()

        curr_q = q_0
        negatives = [] if p_0 in relevance[q_0] else [p_0]

        while True:
            try:
                q, _, p, _, _, _ = next(lines).strip().split()
                if q != curr_q:
                    negatives = negatives[:depth]
                    random.shuffle(negatives)
                    yield curr_q, relevance[curr_q], negatives[:n_sample]
                    curr_q = q
                    negatives = [] if p in relevance[q] else [p]
                else:
                    if p not in relevance[q]:
                        negatives.append(p)
            except StopIteration:
                negatives = negatives[:depth]
                random.shuffle(negatives)
                yield curr_q, relevance[curr_q], negatives[:n_sample]
                return


random.seed(datetime.now().timestamp())
parser = ArgumentParser()
parser.add_argument("--tokenizer_name", required=True)
parser.add_argument("--hn_file", required=True)
parser.add_argument("--qrels", required=True)
parser.add_argument("--queries", required=True)
parser.add_argument("--collection", required=True)
parser.add_argument("--save_to", required=True)
parser.add_argument("--doc_template", type=str, default=None)
parser.add_argument("--query_template", type=str, default=None)

parser.add_argument("--truncate", type=int, default=128)
parser.add_argument("--n_sample", type=int, default=30)
parser.add_argument("--depth", type=int, default=200)
parser.add_argument("--mp_chunk_size", type=int, default=500)
parser.add_argument("--shard_size", type=int, default=45000)

# parser.add_argument("--tokenizer_name", default='t5-base')
# parser.add_argument("--hn_file", default="D:/Proj/embedded_reranking/OpenMatchV2/marco/t5/train.trec")
# parser.add_argument("--qrels", default="D:/Proj/embedded_reranking/OpenMatchV2/marco/qrels.train.tsv")
# parser.add_argument("--queries", default="D:/Proj/embedded_reranking/OpenMatchV2/marco/train.query.txt")
# parser.add_argument("--collection", default="D:/Proj/embedded_reranking/OpenMatchV2/marco/corpus.tsv")
# parser.add_argument("--save_to", default="D:/Proj/embedded_reranking/OpenMatchV2/msmarco/t5/")
# parser.add_argument("--doc_template", type=str, default="Title: <title> Text: <text>")
# parser.add_argument("--query_template", type=str, default=None)
#
# parser.add_argument("--truncate", type=int, default=128)
# parser.add_argument("--n_sample", type=int, default=30)
# parser.add_argument("--depth", type=int, default=200)
# parser.add_argument("--mp_chunk_size", type=int, default=500)
# parser.add_argument("--shard_size", type=int, default=45000)

args = parser.parse_args()

qrel = TrainPreProcessor.read_qrel(args.qrels)
tokenizer = AutoTokenizer.from_pretrained(args.tokenizer_name, use_fast=True)
processor = TrainPreProcessor(
    query_file=args.queries,
    collection_file=args.collection,
    tokenizer=tokenizer,
    doc_max_len=args.truncate,
    doc_template=args.doc_template,
    query_template=args.query_template,
    allow_not_found=True,
)

counter = 0
shard_id = 0
f = None
os.makedirs(args.save_to, exist_ok=True)

pbar = tqdm(load_ranking(args.hn_file, qrel, args.n_sample, args.depth))
with Pool() as p:
    for x in p.imap(processor.process_one, pbar, chunksize=args.mp_chunk_size):
        counter += 1
        if f is None:
            f = open(os.path.join(args.save_to, f"split{shard_id:02d}.hn.jsonl"), "w")
            pbar.set_description(f"split - {shard_id:02d}")
        f.write(x + "\n")

        if counter == args.shard_size:
            f.close()
            f = None
            shard_id += 1
            counter = 0

if f is not None:
    f.close()
