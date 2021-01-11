import subprocess
import os
import sys
import json
import shutil

tmp_dir = os.path.expanduser('~/TMP')
dicts_path = os.path.expanduser('~/dicts')
info_dict_path = os.path.expanduser('~/info_conv_filtered.json')
result_path = os.path.expanduser('~/ape_result')
motif_dir = os.path.expanduser('~/cisbp_conv')

dict_types = ['direct', 'inferred', 'family', 'tf_class_family', 'tf_class_subfamily']


def check_dir_for_collection(tf, motif_collection, d_type):
    dir_path = os.path.join(tmp_dir, tf + '_' + d_type)
    if os.path.exists(dir_path):
        shutil.rmtree(dir_path)
    os.mkdir(dir_path)
    for motif in motif_collection:
        shutil.copy2(os.path.join(motif_dir, motif + '.ppm'), dir_path)
    return dir_path


def parse_output(exp, output):
    pcm_name = os.path.splitext(os.path.basename(exp))[0]
    for line in output.split('\n'):
        if line.startswith('#') or not line:
            continue
        motif, similarity, shift, overlap, orientation = line.strip('\n').split('\t')
        return pcm_name, {'motif': motif, 'similarity': similarity, 'shift': shift, 'overlap': overlap, 'orientation': orientation}
    return pcm_name, {}


def run_ape(exps, res_dir):
    result = {}
    for exp in exps:
        out = subprocess.check_output(["java", '-cp', os.path.expanduser('~/ape.jar'),
                                      'ru.autosome.macroape.ScanCollection', exp, res_dir, '--query-pcm'])
        res = out.decode('utf-8')
        name, res = parse_output(exp, res)
        result[name] = res
    shutil.rmtree(res_dir)
    return result


def read_dicts():
    dicts = {}
    for d_type in dict_types:
        with open(os.path.join(dicts_path, d_type + '_dict.json')) as f:
            dicts[d_type] = json.loads(f.readline())
    return dicts


def transform_name(tf):
    return tf[:-6] if tf.endswith('_HUMAN') else tf


def main():
    dicts = read_dicts()
    with open(info_dict_path) as info:
        info_dict = json.loads(info.readline())
    tf = sys.argv[1]
    print('Now doing {}'.format(tf))
    results = {}
    pwms = [x['pcm_path'] for x in info_dict[tf] if x['pcm_path']]
    t_name = transform_name(tf)
    for d_type in dict_types:
        motif_collection = dicts[d_type].get(t_name)
        if not motif_collection:
            print('not_found:', tf, d_type)
            continue
        res_dir = check_dir_for_collection(tf, motif_collection, d_type)
        ape_res = run_ape(pwms, res_dir)
        results[d_type] = ape_res
    with open(os.path.join(result_path, tf + '.json'), 'w') as out:
        json.dump(results, out)


if __name__ == '__main__':
    main()
