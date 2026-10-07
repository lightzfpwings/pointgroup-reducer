"""用用户指定的原程序核验对齐 JSON；不修改原程序，不是桌面运行依赖。

python verify_with_reducer.py --reducer-path /path/to/pointgroup-reducer --input aligned.json
输入可以是单个对齐对象，或用于回归核验的对象列表。
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys


def verify(data, core, source):
    if data.get('application') != 'basis-character-reducer-bridge' or data.get('schema_version') != 1:
        raise ValueError('需要本模块导出的对齐 JSON。')
    if data.get('characters_weighted') is not False:
        raise ValueError('c 必须是未乘类大小的特征标。')
    table = core.get_table(data['point_group'])
    if table.classes != data['classes'] or table.sizes.tolist() != data['class_sizes'] or table.h != data['h']:
        raise ValueError('原程序共轭类约定已改变，请先重新对齐。')
    hashes = data['target_provenance']['sourceSHA256']
    for name, expected in hashes.items():
        if hashlib.sha256((source / name).read_bytes()).hexdigest() != expected:
            raise ValueError('原程序源文件与已核对快照不同：' + name)
    outputs = []
    for row in [{'id': 'total', 'dimension': data['dimension'], 'c': data['c']}, *data['blocks']]:
        result = table.reduce(row['c'])
        if not result['valid'] or abs(result['dimension'] - row['dimension']) > 1e-7:
            raise ValueError('原程序约化核验失败：' + row['id'])
        outputs.append({'id': row['id'], 'dimension': row['dimension'],
                        'decomposition': table.decomposition(result),
                        'multiplicities': [int(n) for n in result['integer_a']],
                        'integerResidual': result['integer_residual']})
    return {'point_group': table.name, 'status': 'passed', 'vectors': outputs}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reducer-path', type=Path, required=True)
    parser.add_argument('--input', type=Path, required=True)
    args = parser.parse_args()
    source = args.reducer_path.resolve()
    if not (source / 'core.py').is_file():
        raise ValueError('指定目录没有原程序 core.py。')
    sys.path.insert(0, str(source))
    import core
    data = json.loads(args.input.read_text(encoding='utf-8'))
    inputs = data if isinstance(data, list) else [data]
    report = {'status': 'passed', 'originalReducerExecuted': True,
              'groupsOrExamples': len(inputs), 'results': [verify(x, core, source) for x in inputs]}
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
