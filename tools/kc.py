#!/usr/bin/python
import os
import sys
import yaml
from pathlib import Path

def load_yaml_file(filepath):
    with open(filepath, 'r') as file:
        return yaml.safe_load(file)

def save_yaml_file(data, filepath):
    with open(filepath, 'w') as file:
        yaml.safe_dump(data, file, default_flow_style=False)

def update_names(config, filename_prefix, verbose):
    only_one_cluster = False
    if 'clusters' in config and len(config['clusters']) == 1:
        only_one_cluster = True
    if 'clusters' in config:
        for item in config['clusters']:
            original_name = item['name']
            item['name'] = f"{filename_prefix}-{original_name}"
            if only_one_cluster:
                item['name'] = f"{filename_prefix}"
    if 'users' in config:
        for item in config['users']:
            original_name = item['name']
            item['name'] = f"{filename_prefix}-{original_name}"
            if only_one_cluster:
                item['name'] = f"{filename_prefix}"
    if 'contexts' in config:
        for item in config['contexts']:
            cluster_name = item['context']['cluster']
            user_name = item['context']['user']
            item['context']['cluster'] = f"{filename_prefix}-{cluster_name}"
            item['context']['user'] = f"{filename_prefix}-{user_name}"
            item['name'] = f"{filename_prefix}-{item['name']}"
            if only_one_cluster:
                item['context']['cluster'] = f"{filename_prefix}"
                item['context']['user'] = f"{filename_prefix}"
                item['name'] = f"{filename_prefix}"

def combine_configs(directory, verbose):
    combined_config = {'apiVersion': 'v1', 'kind': 'Config', 'clusters': [], 'contexts': [], 'users': [], 'preferences': {}}
    config_dir = Path(directory)
    for config_file in config_dir.glob('*.yaml'):
        if verbose:
            print(f"Processing {config_file}")
        config = load_yaml_file(config_file)
        filename_stem = config_file.stem
        update_names(config, filename_stem, verbose)
        combined_config['clusters'].extend(config.get('clusters', []))
        combined_config['contexts'].extend(config.get('contexts', []))
        combined_config['users'].extend(config.get('users', []))
    return combined_config

def parse_options(args):
    verbose = False
    kubeconfig_path = None
    install = False
    run = False
    try:
        opts, args = getopt.getopt(args, "v", ["verbose", "kubeconfig=", "install", "run"])
    except getopt.GetoptError as err:
        print(err)
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-v", "--verbose"):
            verbose = True
        elif opt == "--kubeconfig":
            kubeconfig_path = arg
        elif opt == '--install':
            install = True
        elif opt == '--run':
            run = True
    return verbose, kubeconfig_path, install, run


def print_help():
    print()
    print("Usage: kc.py [options]")
    print("Options:")
    print("  --install: Install kc.py to ~/.kube/kc.py")
    print("  --run: Combine config files in ~/.kube/config.d and save to ~/.kube/config")
    print("  --kubeconfig: Specify the path to save the combined config file (instead of ~/.kube/config)")
    print("  -v, --verbose: Print more information")
    print()

import getopt
if __name__ == "__main__":
    verbose, override_kubeconfig_path, install, run = parse_options(sys.argv[1:])
    home_dir = Path.home()
    default_config_directory = home_dir / '.kube' / 'config.d'
    default_kubeconfig_path = home_dir / '.kube' / 'config'
    if install:
        cur_location = Path(__file__).resolve()
        kubeconfig_dir = home_dir / '.kube'
        kubeconfig_dir.mkdir(exist_ok=True)
        kc_location = kubeconfig_dir / 'kc.py'
        kc_location.write_text(cur_location.read_text())
        ## make executable
        os.chmod(kc_location, 0o755)
        print(f'''kc.py installed to {kc_location}.\nUse:
              
              * Now place all your configfiles in {default_config_directory}. make sure they have a .yaml file extension.
              * Back up your existing .kube/config
              * `{kc_location} --run` to combine them into {default_kubeconfig_path}
''')
        default_config_directory.mkdir(exist_ok=True)

        sys.exit(0)

    elif run:
        config_directory = str(default_config_directory)
        output_config_path = str(override_kubeconfig_path or default_kubeconfig_path)

        combined_config = combine_configs(config_directory, verbose)
        if len(combined_config['clusters']) == 0:
            print("No clusters found in config files, not overwriting kubeconfig file. Exiting.")
            sys.exit(1)
        save_yaml_file(combined_config, output_config_path)

        if verbose:
            print(f"Combined config saved to {output_config_path}")

    else:
        print_help()
        sys.exit(1)
