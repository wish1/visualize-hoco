import json
import os
import sys
from base64 import b64encode
from drawlogo import start
import requests
from flask import render_template, Flask
from cairosvg import svg2png

app = Flask(__name__)


def get_image_code(svg):
    if svg.startswith('http'):
        r = requests.get(svg)
        result = r.content
    else:
        with open(svg, 'rb') as svg_image:
            result = svg_image.read()

        # os.remove(svg)
    return 'data:image/png;base64,' + b64encode(result).decode('ascii')


def draw_svg(pcm_path):
    directory = os.path.expanduser('~/svgs')
    out_path = os.path.join(directory, os.path.basename(pcm_path))
    if not os.path.isdir(directory):
        os.mkdir(directory)
    start.draw_logo(pcm_path,
                    out_path=out_path,
                    unit_height=80,
                    unit_width=40)
    svg2png(url=out_path, write_to=out_path, output_height='30', dpi=10)
    return out_path


def get_image_code_for_json(tfs_dict):
    for t_factor in tfs_dict:
        for index, exp in enumerate(tfs_dict[t_factor]):
            if index % 100 == 0:
                print('Done {} motifs for {}'.format(index, t_factor))
            if exp.get('motif_image') is None:
                exp['motif_image'] = draw_svg(exp['pcm_path'])
            exp['motif_image'] = get_image_code(exp['motif_image'])


@app.route('/hoco/<name>')
def hello(name=None, dictionary=None):
    if dictionary is None:
        dictionary = {
           'CTCF': [
               {
                   'name': 'PEAK456',
                   'caller': 'macs',
                   'motif_type': 'single',
                   'selected_by': 'P-value',
                   'motif_index': 0,
                   'motif_len': 4,
                   'time': '26m',
                   'diag': [],
                   'motif_image': 'http://greco-bit.informatik.uni-halle.de:8080/motifs/motif2557.svg'
               },
               {
                   'name': 'PEAK456',
                   'caller': 'gem',
                   'selected_by': 'Score',
                   'motif_type': 'flat',
                   'motif_index': 0,
                   'time': '16h',
                   'motif_len': 23,
                   'motif_image': 'http://greco-bit.informatik.uni-halle.de:8080/motifs/motif2558.svg'
               }
           ],
        }
    get_image_code_for_json(dictionary)
    tf_data = dictionary.get(name)
    if not name or not tf_data:
        return 'Error', 404
    return render_template('tf_analysis.html', tf_data=tf_data, name=name, length=len(tf_data))


if __name__ == '__main__':
    tfs_stats = sys.argv[1] if len(sys.argv) > 1 else None
    if tfs_stats is not None:
        with app.app_context():
            with open(tfs_stats) as opened_json:
                d = json.loads(opened_json.readline())
                for tf in d.keys():
                    with open(os.path.expanduser('~/report/{}.html'.format(tf)), 'w') as out:
                        print('Saving {}'.format(tf))
                        out.write(hello(tf, dictionary=d))
    else:
        app.run(debug=True, host='0.0.0.0', port=8000)
