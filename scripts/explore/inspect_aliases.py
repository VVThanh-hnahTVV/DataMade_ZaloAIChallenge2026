import json

for l in open('train/answers.jsonl'):
    x = json.loads(l)
    if x['alias'] and x['type'] in ('string', 'list', 'table'):
        print(x['type'], x['answer'], x['alias'])