# -*- coding: utf-8 -*-
"""
This script create a file (pipfreeze.txt) with the pip freeze command and 
compare it with the requirements_pysv.txt and show the module version differences.

@author: Carlos
"""
import subprocess
import os
try:
    from packaging import version
except ImportError:
    https='https://intelpypi.intel.com/pythonsv/production'
    #https = 'http://proxy-chain.intel.com:912'
    subprocess.call(['python', '-m', 'pip', 'download', 'packaging','-i', https])
    packaging_file = next((f for f in os.listdir('.') if f.startswith('packaging') and f.endswith('.whl')), None)
    #pyparsing_file = next((f for f in os.listdir('.') if f.startswith('pyparsing') and f.endswith('.whl')), None)
    if packaging_file:
        subprocess.call(['pip', 'install', packaging_file])
    # if pyparsing_file:
        # subprocess.call(['pip', 'install', pyparsing_file])
        from packaging import version

def generate_pip_freeze(file_name):
    with open(file_name, "w") as f:
        subprocess.call(["pip", "freeze"], stdout=f)


def get_silicon_family():
    projects = {"SPR": "sapphirerapids", "CLX": "cascadelakex"}
    #siliconfamily = "SPR"  # DEBUG
    siliconfamily = os.environ.get('SiliconFamily')
    if siliconfamily is None:
        print("The Siliconfamily is not set in config file.")
        return None
    else:
        project_name = projects.get(siliconfamily.upper())
        if project_name:
            return project_name
        else:
            print("project need to be set in projects dictionary")
            return None


def clear_screen():
    if os.name == "posix":
        subprocess.call("clear", shell=True)
    elif os.name == "nt":
        subprocess.call("cls", shell=True)


def read_file_to_dict(file_name):
    package_dict = {}
    with open(file_name, "r") as f:
        lines = f.readlines()
    for line in lines:
        stripped_line = line.strip()
        if stripped_line and not stripped_line.startswith("#"):
            operator = None
            if "==" in stripped_line:
                operator = "=="
            elif ">=" in stripped_line:
                operator = ">="
            elif "<=" in stripped_line:
                operator = "<="
            elif ">" in stripped_line:
                operator = ">"
            elif "<" in stripped_line:
                operator = "<"

            if operator:
                package_name, package_version = stripped_line.split(operator)
                package_dict[package_name.strip()] = (
                    operator,
                    package_version.strip(),
                )
    return package_dict


def compare_versions(pipfreeze_version, operator, version_num):
    pipfreeze_version_parsed = version.parse(pipfreeze_version)
    version_num_parsed = version.parse(version_num)

    if operator == "==" and pipfreeze_version_parsed != version_num_parsed:
        return pipfreeze_version_parsed, operator, version_num_parsed
    elif operator == ">=" and pipfreeze_version_parsed < version_num_parsed:
        return pipfreeze_version_parsed, operator, version_num_parsed
    elif operator == "<=" and pipfreeze_version_parsed > version_num_parsed:
        return pipfreeze_version_parsed, operator, version_num_parsed
    elif operator == ">" and pipfreeze_version_parsed <= version_num_parsed:
        return pipfreeze_version_parsed, operator, version_num_parsed
    elif operator == "<" and pipfreeze_version_parsed >= version_num_parsed:
        return pipfreeze_version_parsed, operator, version_num_parsed
    else:
        return False


def main(pipfreeze_file, requirements_file):
    generate_pip_freeze(pipfreeze_file)
    print("\nCreating pipfreeze.txt with all modules installed.\n")
    clear_screen()

    pipfreeze_dict = read_file_to_dict(pipfreeze_file)
    requirements_dict = read_file_to_dict(requirements_file)

    differences = []

    for package_name, (operator, version_num) in requirements_dict.items():
        if package_name in pipfreeze_dict:
            pipfreeze_version = (
                pipfreeze_dict[package_name][1]
                if isinstance(pipfreeze_dict[package_name], tuple)
                else pipfreeze_dict[package_name]
            )
            if compare_versions(pipfreeze_version, operator, version_num):
                differences.append(
                    (
                        "{}=={}".format(package_name, pipfreeze_version),
                        "{}{}{}".format(package_name, operator, version_num),
                    )
                )

    if differences:
        print("Differences found:")
        print("-" * 80)
        print("{:<32} | {:>32}".format(pipfreeze_file, requirements_file))
        print("-" * 80)

        for pipfreeze_entry, requirements_entry in differences:
            # print(f"{pipfreeze_entry:<32} | {requirements_entry:>32}")
            print(
                "{:<32} | {:>32}".format(pipfreeze_entry, requirements_entry)
            )
    else:
        print("No differences found")


if __name__ == "__main__":
    pipfreeze_file = r"pipfreeze.txt"
    get_project_directory = get_silicon_family()
    # requirements_file = (r"D:\Python_Training\check_requirements\requires_pysv.txt") #DEBUG
    requirements_file = os.path.join(
        "C:\\", "pythonsv", get_project_directory, "requires_pysv.txt"
    )
    main(pipfreeze_file, requirements_file)
