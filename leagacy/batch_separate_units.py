import sys
import os
import glob
from optparse import OptionParser, OptionGroup
import re

def invert_dict(orig):
    inverted = {}
    for key in list(orig.keys()):
        for v in orig[key]:
            if v not in inverted:
                inverted[v] = []
            inverted[v].append(key)

    return inverted

if __name__=='__main__':
    klee_command = 'klee --simplify-sym-indices --write-cvcs --write-cov --output-module --max-memory=1000 --disable-inlining --optimize --use-forked-solver --use-cex-cache --libc=uclibc --posix-runtime --allow-external-sym-calls --only-output-states-covering-new --max-sym-array-size=4096 --max-instruction-time=60. --max-time=3600. --watchdog --max-memory-inhibit=false --max-static-fork-pct=1 --max-static-solve-pct=1 --max-static-cpfork-pct=1 --switch-type=internal --randomize-fork --search=random-path --search=nurs:covnew --use-batching-search --batch-instructions=10000 '
    klee_executable = ' ./ngircd '
    klee_sym_args = '' #' --sym-args 0 1 10 --sym-args 0 2 2 --sym-files 1 8 '
    decl_vars = []
    func_nodes = []

    inj_code = []
    func_names = []

    parser = OptionParser("usage: %prog -d {directory containing source files} -e {executable name}")
    parser.add_option('-d', '--dir', action='store', type='string', dest='dir', help='Source file directory path')
    parser.add_option('-e', '--exec', action='store', type='string', dest='executable', help='Name of executable generated by Makefile')

    (opts, args) = parser.parse_args()

    # pprint(('diags', map(get_diag_info, tu.diagnostics)))

    dir_name = opts.dir
    exec_name = opts.executable

    if not os.path.isdir(dir_name):
        print('Could not find the specified directory.\nExiting.')
        sys.exit(-1)

    if not dir_name.endswith('/'):
        dir_name = dir_name+'/'
    
    caller_dict = {}

    for f in glob.glob(dir_name+'*.c'):
        if os.path.exists(f[:-2]+'_units'):
            print('Unit files for ' + f[:-2] + ' exists')
            continue
        print(f)
        os.system('python generate_separate_unit.py -f '+f+' -a')
    
    for f in glob.glob(dir_name+'*.c'):
        base_f = f[:-2]
        unit_name = os.path.splitext(os.path.basename(f))[0]
        if not os.path.isdir(base_f+'_units'):
            print('No unit test directory generated for ' + f)
            continue
        for callee in glob.glob(base_f+'_units/'+unit_name+'_*.c.callee'):
            callee_file = open(callee, 'r')
            
            # "If regular expressions is the solution to your problem, then you have two problems" - Some dude
            
            re_pattern = base_f+'_units/'+unit_name+'_(.*)\.c\.callee'
            re_match = re.search(re_pattern, callee)
            key = re_match.group(1)
            
            for line in callee_file:
                if not line.strip()=='':
                    if key not in list(caller_dict.keys()):
                        caller_dict[key] = []
                    caller_dict[key].append(line.strip())

    inverted_caller_dict = invert_dict(caller_dict)
    
    for f in glob.glob(dir_name+'*.c'):
        base_f = f[:-2]
        unit_name = os.path.splitext(os.path.basename(f))[0]
        if not os.path.isdir(base_f+'_units'):
            print('No unit test directory generated for ' + f)
            continue
        
        for callee in glob.glob(base_f+'_units/'+unit_name+'_*.c.units'):
            re_pattern = base_f+'_units/'+unit_name+'_(.*)\.c\.units'
            re_match = re.search(re_pattern, callee)
            key = re_match.group(1)
            
            caller_file = open(base_f+'_units/'+unit_name+'_'+key+'.c.caller', 'w')
            caller_list = inverted_caller_dict[key]if (key in list(inverted_caller_dict.keys())) else []
            
            for v in caller_list:
                if not v=='': 
                    caller_file.write(v+'\n')
            

