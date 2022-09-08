# Adapted from Tevatron (https://github.com/texttron/tevatron)

import json
import os
from argparse import ArgumentParser

from transformers import AutoTokenizer, PreTrainedTokenizer
from tqdm import tqdm
from openmatch.utils import fill_template

parser = ArgumentParser()
parser.add_argument('--input', type=str, required=True)
parser.add_argument('--output', type=str, required=True)
parser.add_argument('--query_template', type=str)
parser.add_argument('--doc_template', type=str)
parser.add_argument('--tokenizer', type=str, required=False, default='bert-base-uncased')
parser.add_argument('--minimum-negatives', type=int, required=False, default=1)
args = parser.parse_args()

tokenizer: PreTrainedTokenizer = AutoTokenizer.from_pretrained(args.tokenizer, use_fast=True)

data = json.load(open(args.input))

save_dir = os.path.split(args.output)[0]
if not os.path.exists(save_dir):
    os.makedirs(save_dir)

with open(args.output, 'w') as f:
    for idx, item in enumerate(tqdm(data)):
        if len(item['hard_negative_ctxs']) < args.minimum_negatives or len(item['positive_ctxs']) < 1:
            continue

        group = {}
        positives = []
        for pos in item['positive_ctxs']:
            positives.append(fill_template(args.doc_template, pos))
        negatives = []
        for neg in item['hard_negative_ctxs']:
            negatives.append(fill_template(args.doc_template, neg))

        query = tokenizer.encode(fill_template(args.query_template, item), add_special_tokens=False, max_length=32, truncation=True)
        positives = tokenizer(
            positives, add_special_tokens=False, max_length=128, truncation=True, padding=False)['input_ids']
        negatives = tokenizer(
            negatives, add_special_tokens=False, max_length=128, truncation=True, padding=False)['input_ids']

        group['query'] = query
        group['positives'] = positives
        group['negatives'] = negatives

        f.write(json.dumps(group) + '\n')
