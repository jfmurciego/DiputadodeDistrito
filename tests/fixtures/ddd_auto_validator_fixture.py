"""Synthetic validator used only by the ddd auto orchestration tests."""
import argparse
import json
from pathlib import Path
import zipfile


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('task',choices=['F03'])
    parser.add_argument('--repo',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--packet',type=Path,required=True)
    args=parser.parse_args()
    with zipfile.ZipFile(args.packet) as archive:
        evidence=json.loads(archive.read('simulation.json'))
    if evidence != {'task':'F03','result':'PASS'}:
        raise SystemExit('Synthetic F03 packet rejected')
    with args.output.open('x',encoding='utf-8') as stream:
        json.dump({'task':'F03','status':'PASS','synthetic_test_fixture_only':True},stream)
        stream.write('\n')


if __name__=='__main__':
    main()
