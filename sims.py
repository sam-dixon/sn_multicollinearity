import os
import click
import numpy as np
import pandas as pd
from iminuit import Minuit

DATA_DIR = os.path.abspath(os.path.join(os.curdir, 'data'))
DF = pd.read_csv(os.path.join(DATA_DIR, 'combined_data.csv'))


def fit_simultaneous(df):
    """Fit 2D linear and step functions simultaneously"""

    def chisq(mag, alpha, beta, gamma):
        model = mag + alpha * df.x1 + beta * df.c + gamma / 2. * np.sign(
            df.mass - 10)
        return np.sum((model - df.mu) ** 2)

    m = Minuit(chisq, mag=0, alpha=0, beta=0, gamma=0,
               pedantic=False, print_level=0)
    m.migrad()
    resids = df.mu - m.values['mag'] - m.values['alpha'] * df.x1 - m.values[
        'beta'] * df.c - m.values['gamma'] / 2. * np.sign(df.mass - 10)

    return m.values, np.std(resids)


def fit_separate(df):
    """Fit 2D linear function and then fit step function on residuals"""

    def lin_chisq(mag, alpha, beta):
        model = mag + alpha * df.x1 + beta * df.c
        return np.sum((model - df.mu) ** 2)

    m_lin = Minuit(lin_chisq, mag=0, alpha=0, beta=0,
                   pedantic=False, print_level=0)
    m_lin.migrad()
    resids = df.mu - m_lin.values['mag'] - m_lin.values['alpha'] * df.x1 - \
             m_lin.values['beta'] * df.c

    def step_chisq(gamma):
        model = gamma / 2. * np.sign(df.mass - 10)
        return np.sum((model - resids) ** 2)

    m = Minuit(step_chisq, gamma=0, pedantic=False, print_level=0)
    m.migrad()

    resids = resids - m.values['gamma'] / 2. * np.sign(df.mass - 10)
    return m_lin.values, m.values, np.std(resids)


def run_sim(alpha=0.14, beta=3.1, gamma=0.8, sig_int=0.6, mag=19.1, nsims=50):
    truth = {'alpha': alpha,
             'beta': beta,
             'gamma': gamma,
             'sig_int': sig_int,
             'mag': mag}

    subset_vals = {k: {'alpha_sep': [],
                       'beta_sep': [],
                       'gamma_sep': [],
                       'sig_int_sep': [],
                       'alpha_sim': [],
                       'beta_sim': [],
                       'gamma_sim': [],
                       'sig_int_sim': []} for k in DF.set.unique()}
    for trial in range(nsims):
        DF['mu'] = mag + alpha * DF.x1 \
                   + beta * DF.c \
                   + gamma / 2. * np.sign(DF.mass - 10) \
                   + np.random.randn(len(DF)) * sig_int
        for subset in DF.set.unique():
            vals_sim, std_resid_sim = fit_simultaneous(DF[DF.set == subset])
            vals_lin, val_step, std_resid_sep = fit_separate(DF[DF.set == subset])
            subset_vals[subset]['alpha_sim'].append(vals_sim['alpha'])
            subset_vals[subset]['beta_sim'].append(vals_sim['beta'])
            subset_vals[subset]['gamma_sim'].append(vals_sim['gamma'])
            subset_vals[subset]['sig_int_sim'].append(std_resid_sim)
            subset_vals[subset]['alpha_sep'].append(vals_lin['alpha'])
            subset_vals[subset]['beta_sep'].append(vals_lin['beta'])
            subset_vals[subset]['gamma_sep'].append(val_step['gamma'])
            subset_vals[subset]['sig_int_sep'].append(std_resid_sep)

    results = []
    for subset, vals in subset_vals.items():
        result = {}
        for param in ['alpha', 'beta', 'gamma', 'sig_int']:
            result[param] = truth[param]
            result['subset'] = subset
            result[param+'_sim'] = np.mean(vals[param+'_sim'])
            result[param+'_sep'] = np.mean(vals[param+'_sep'])
            result[param+'_sim_err'] = np.std(vals[param+'_sim'])
            result[param+'_sep_err'] = np.std(vals[param+'_sep'])
        results.append(result)
    return pd.DataFrame(results)


@click.command()
@click.option('--alpha', default=0.14)
@click.option('--beta', default=3.1)
@click.option('--nsims', default=50)
def main(alpha, beta, nsims):
    gammas = np.linspace(-0.1, 0.1, 3)
    sig_ints = np.linspace(0, 0.1, 3)
    results = []
    for gamma in gammas:
        for sig_int in sig_ints:
            print(gamma, sig_int)
            results.append(run_sim(alpha, beta, gamma, sig_int, nsims=nsims))
    results_df = pd.concat(results, ignore_index=True)
    result_fname = '{}_{}.csv'.format(alpha, beta)
    result_path = os.path.join(DATA_DIR, result_fname)
    results_df.to_csv(result_path)

if __name__ == '__main__':
    main()