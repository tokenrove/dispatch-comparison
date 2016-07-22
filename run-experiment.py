#!/usr/bin/env python2

import os, sys, argparse, subprocess, datetime, random

class Experiment(argparse.Namespace): pass
class Trial(argparse.Namespace): pass

def die(s):
    raise Exception(s)

def hostname():
    return subprocess.check_output(['hostname']).strip()

def ensure_dir(path):
    """mkdir -p"""
    try:
        os.makedirs(path)
    except OSError as e:        # ugh, python3 does this better
        if 17 != e.errno: raise

def ensure_results_directory(opt):
    """Make a directory named host-date under opt.output_path, returning
    the path."""
    date = datetime.datetime.now().strftime('%y%m%d')
    dirname = '{}-{}'.format(hostname(), date)
    path = os.path.join(opt.output_path, dirname)
    ensure_dir(path)
    return path

results = {}
def validate_exit_code(code, trial, opt):
    k = trial.experiment.path
    if not results.has_key(k):
        results[k] = code
    if code != results[k]:
        die("Result didn't match for trial {}".format(trial.path))

def aggregate_individual_results(t, opt):
    pass

def run_perf_tool(t, run, opt):
    if opt.perf_tool == 'perf':
        cmd = ['perf', 'stat', '-x,']
    else:
        die("Not sure how to deal with {}".format(opt.perf_tool))
    cmd += [t.path, str(opt.n_dispatches)]
    if opt.verbose: print ' '.join(cmd)
    with open("{}-run-{}".format(t.path, run), "w") as f:
        return subprocess.call(cmd, stderr=f)

def run_trials(trials, opt):
    """Shuffle trials, running each one opt.n_runs times under
    opt.perf_tool."""
    random.shuffle(trials)
    for t in trials:
        for i in range(opt.n_runs):
            code = run_perf_tool(t, i, opt)
            if opt.verbose: print "{} returned {}".format(t.path, code)
            validate_exit_code(code, t, opt)
        aggregate_individual_results(t, opt)

def analyze_results(opt):
    """TODO: analyze output; output pretty graphs."""
    # do simple least-squares minimization
    # output pretty graphs
    pass

# XXX Linux-only
def populate_host_information(opt):
    with open('host-info', 'w') as o:
        o.write(subprocess.check_output(['uname', '-a']))
        o.write("\n")

        o.write(subprocess.check_output(['vmstat', '-s']))
        o.write("\n")

        with open('/proc/cpuinfo') as i:
            o.write(i.read())

def setup_results_directory(opt):
    path = ensure_results_directory(opt)
    os.chdir(path)
    populate_host_information(opt)
    return path

def generate(experiment, strategies, opt):
    d = os.getcwd()
    os.chdir(experiment.path)
    args = [os.path.join(opt.template_path, 'generator'),
            '--n-entries', experiment.n_entries,
            '--cache-flush', experiment.cache_flush,
            '--fn-alignment', experiment.fn_alignment,
            'dummy-fns.c', 'dummy-fns.h']
    cmd = map(str, args) + map(src_of_strategy, strategies)
    if opt.verbose: print ' '.join(cmd)
    subprocess.check_call(cmd)
    os.chdir(d)

def src_of_strategy(s):
    return {'c-vtable': 'c-vtable.c',
            'c-switch': 'c-switch.c',
            'linear': '{arch}-linear.s',
            'binary': '{arch}-binary.s',
            'vtable': '{arch}-vtable.s'}[s].format(arch='x86_64')

# Originally I had a Makefile to do this stuff, but I realized that I
# wanted to explicitly rebuild everything every time anyway, so why
# not do it through Python?
def build_trial(trial, opt):
    cc_flags = '-Wall -Wextra -std=gnu11 -O3 -mtune=native -march=native -g'.split()
    ld_flags = '-lm'.split()
    driver_objs = ['main.c',
                   'ns-{}.c'.format(trial.experiment.distribution)]
    # build gcc -o trial trial dummy-fns main ns-distribution
    build_cmd = ['gcc'] + cc_flags + ['-o', trial.path]
    build_cmd += ['-DN_ENTRIES={}'.format(trial.experiment.n_entries),
                  '-I{}'.format(opt.template_path)]
    build_cmd += [os.path.join(opt.template_path, x) for x in driver_objs]
    d = os.path.dirname(trial.path)
    build_cmd += [os.path.join(d, x) for x in [trial.source, 'dummy-fns.c']]
    build_cmd += ld_flags
    if opt.verbose: print ' '.join(build_cmd)
    subprocess.check_call(build_cmd)

def build_trials(factors, opt):
    experiments = [Experiment(n_entries=n, cache_flush=cf, distribution=d, fn_alignment=fa)
                   for n in factors['n_entries']
                   for cf in factors['cache_flush']
                   for d in factors['distribution']
                   for fa in factors['fn_alignment']]
    trials = []
    strategies = factors['strategy']
    for e in experiments:
        e.path = '{}-{}-{}-{}'.format(e.n_entries, e.cache_flush, e.distribution, e.fn_alignment)
        ensure_dir(e.path)
        generate(e, strategies, opt)
        for s in strategies:
            src = src_of_strategy(s)
            t = Trial(path='./{}/{}'.format(e.path, s), source=src, experiment=e, strategy=s)
            if opt.build_p:
                build_trial(t, opt)
            if not os.path.exists(t.path):
                die("{} doesn't exist; this probably isn't going to work out for you.".format(t.path))
            trials.append(t)
    # for the combinations of the chosen factors
    #   mkdir factor-combination
    #   generate and build the relevant programs
    return trials

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('factors', nargs='+',
                        choices=['strategy','n_entries','cache_flush',
                                 'distribution', 'fn_alignment'])
    parser.add_argument('--n-runs', dest='n_runs', type=int, default=5)
    parser.add_argument('--n-dispatches', type=int, default=100000)
    parser.add_argument('--perf-tool', choices=['perf','cachegrind'], default='perf')
    parser.add_argument('--template-path', default=os.path.dirname(os.path.realpath(__file__)))
    parser.add_argument('--output-path', default=os.getcwd())
    parser.add_argument('--build', dest='build_p', default=True)
    parser.add_argument('--run', dest='run_p', default=True)
    parser.add_argument('--dont-build', dest='build_p', action='store_false')
    parser.add_argument('--dont-run', dest='run_p', action='store_false')
    parser.add_argument('--verbose', action='store_true')
    opt = parser.parse_args()

    # for each factor, we have a range of values
    factors = {
        'strategy': ['c-vtable', 'c-switch', 'linear', 'binary', 'vtable'],
        #'n_entries': [2, 4, 8, 16, 256, 1024, 65536],
        'n_entries': [2, 16, 1024],
        #'cache_flush': ['none', 'I', 'D', 'ID'],
        'cache_flush': ['none'],
        'distribution': ['constant', 'sequential', 'uniform', 'pareto'],
        #'fn_alignment': ['default', '16', '32', '64']
        'fn_alignment': ['default'],
    }
    setup_results_directory(opt)

    trials = build_trials(factors, opt)
    if opt.run_p:
        run_trials(trials, opt)
    analyze_results(opt)

if __name__ == '__main__': main()
