import os
import numpy as np

SCRIPT_DIR = os.path.join(os.curdir, 'scripts')
SUBMIT_PATH = os.path.join(SCRIPT_DIR, 'submit_all.sh')
LOG_DIR = os.path.join(os.curdir, 'logs')
os.makedirs(SCRIPT_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)
os.chmod(SCRIPT_DIR, 0o0755)
os.chmod(LOG_DIR, 0o0755)


TEMPLATE = """#!/bin/bash
#$ -N mc_{alpha}_{beta}
#$ -e {curr_dir}/logs
#$ -o {curr_dir}/logs
/home/samdixon/anaconda3/bin/python {curr_dir}/sims.py --alpha {alpha} --beta {beta}"""


alphas = np.linspace(0.05, 0.2, 11)
betas = np.linspace(2.5, 3.5, 11)
for alpha in alphas:
    for beta in betas:
        script_fname = '{:03.0f}_{:02.0f}.sh'.format(alpha*1000, beta*10)
        script_path = os.path.join(SCRIPT_DIR, script_fname)
        with open(script_path, 'w') as f:
            props = {'alpha': np.round(alpha, 2),
                     'beta': np.round(beta, 1),
                     'curr_dir': os.path.abspath(os.curdir)}
            f.write(TEMPLATE.format(**props))
        with open(SUBMIT_PATH, 'a') as f:
            f.write('qsub {}\n'.format(script_path))
            f.write('sleep 0.5\n')
os.chmod(SUBMIT_PATH, 0o755)

