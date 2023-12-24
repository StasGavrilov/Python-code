#!/usr/bin/python3

import subprocess
import argparse
import importlib
import urllib.request

class ConsolePrinter:
    def print_success(self, message):
        print(f'\033[92m{message}\033[0m')

    def print_failure(self, message):
        print(f'\033[91m{message}\033[0m')

    def print_installing(self, message):
        print(f'\033[93m{message}\033[0m')

class PackageManager:
    def __init__(self):
        self.base_command = 'sudo apt-get install -y'
        self.pip3_base_command = 'pip3 install -y'
        self.packages = ['update', 'python3-pip', 'tmux', 'ipmitool', 'smartctl', 'rpm', 'screen', 'alien', 'python3-venv', 'sshpass', 'nfs-common', 'pexpect', 'isoweek', 'httplib2', 'vim', 'libpci']
        self.python_packages = ['pexpect', 'isoweek', 'httplib2', 'libpci']
        self.ilo_rpm_path = 'ilorest-4.6.0.0-11.x86_64.rpm'
        self.ilo_install_cmd = ['sudo', 'alien', '-i', self.ilo_rpm_path]
        self.ilorest_url = 'http://dist/hardware/Hardware_tools/ilorest-4.6.0.0-11.x86_64.rpm'
        self.ilorest_rpm_file = 'ilorest-4.6.0.0-11.x86_64.rpm'
        self.suplogs = [['sudo', 'mkdir', '-p', '/root/suplogs'], ['sudo', 'mount', '-t', 'nfs', 'ibox3001-nas.lab.gdc.il.infinidat.com:/suplogs', '/root/suplogs']]
        self.hwnotify = 'git clone https://git.infinidat.com/germanv/hw_notify.git && cd hw_notify && make install'
        self.printer = ConsolePrinter()

    def check_install_package(self, packages, python_packages=None):
        if python_packages is None:
            python_packages = []

        for package in packages:
            if package in python_packages:
                try:
                    importlib.import_module(package)
                    self.printer.print_success(f"{package} is already installed.")
                except ImportError:
                    self.printer.print_failure(f"{package} is not installed.")
                    self.printer.print_installing(f"Installing...")
                    self.install_python_packages([package])
            else:
                try:
                    subprocess.run(['dpkg', '-s', package], check=True)
                    self.printer.print_success(f"{package} is already installed.")
                except subprocess.CalledProcessError:
                    self.printer.print_failure(f"{package} is not installed.")
                    self.printer.print_installing(f"Installing...")
                    self.install_packages([package])

    def install_packages(self, packages):
        for package in packages:
            try:
                subprocess.run(self.base_command + [package], shell=True)
                self.printer.print_success(f'Success! {package} installed successfully!')
            except subprocess.CalledProcessError:
                self.printer.print_failure(f"Failed to install {package}...")

    def install_python_packages(self, python_packages):
        for package in python_packages:
            try:
                subprocess.run(self.pip3_base_command + [package], shell=True)
                self.printer.print_success(f'Success! {package} installed successfully!')
            except subprocess.CalledProcessError:
                self.printer.print_failure(f"Failed to install {package}...")

    def download_ilorest_rpm(self, url, ilorest_rpm_file):
        try:
            urllib.request.urlretrieve(url, ilorest_rpm_file)
            self.printer.print_success(f'Success! {ilorest_rpm_file} downloaded.')
        except Exception as e:
            self.printer.print_failure(f"Failed to download ILORest RPM from {url}: {str(e)}")

    def install_ilorest(self):
        try:
            subprocess.run(self.ilo_install_cmd, check=True, shell=True)
            self.printer.print_success('Success! ILORest installed successfully!')
        except subprocess.CalledProcessError:
            self.printer.print_failure("Failed to install ILORest...")

    def install_suplogs(self, suplogs):
        success = True
        for cmd in suplogs:
            try:
                subprocess.run(cmd, check=True, shell=True)
            except subprocess.CalledProcessError:
                success = False
                self.printer.print_failure("Failed to install Suplogs...")

        if success:
            self.printer.print_success('Success! Suplogs installed successfully!')

    def hw_notify(self):
        try:
            self.printer.print_failure(f"Note: You will be needed to enter your Git username/password manually.")
            subprocess.run(self.hwnotify, shell=True, check=True)
        except Exception as e:
            self.printer.print_failure(f"Failed to install hwnotify: {str(e)}")
        else:
            self.printer.print_success('Success! hwnotify installed successfully!')

class Authorized:
    def __init__(self):
        self.mfg = ('sshpass -p xsignnet1 scp -o StrictHostKeyChecking=no -r root@hardware-vm:/root/.ssh/mfg_root_id ~/.ssh/', 'mfg_root_id')
        self.id = ('sshpass -p xsignnet1 scp -o StrictHostKeyChecking=no -r root@hardware-vm:/root/.ssh/id_rsa ~/.ssh/', 'id_rsa')
        self.config = ('sshpass -p xsignnet1 scp -o StrictHostKeyChecking=no -r root@hardware-vm:/root/.ssh/config ~/.ssh/', 'config')
        self.printer = ConsolePrinter()

    def copy_keys(self):
        commands = [self.mfg, self.id, self.config]

        for command, filename in commands:
            success = self._run_command(command)
            status = 'Succeeded to copy' if success else 'Failed to copy'
            if success:
                self.printer.print_success(f'{status} {filename}.')
            else:
                self.printer.print_failure(f'{status} {filename}.')

    def _run_command(self, command):
        try:
            subprocess.run(command, shell=True, check=True)
            return True
        except subprocess.CalledProcessError:
            return False

if __name__ == "__main__":
    package_manager = PackageManager()
    authorized = Authorized()
    printer = ConsolePrinter()

    parser = argparse.ArgumentParser(description='Script for VM and laptop operations.')
    parser.add_argument('-v', '--vm', dest='vm', action='store_true', help='Perform operations for VM.')
    parser.add_argument('-l', '--laptop', dest='laptop', action='store_true', help='Perform operations for laptop.')
    parser.add_argument('-p', '--packages', dest='packages', action='store_true', help='Perform package installation only.')
    parser.add_argument('-s', '--suplogs', dest='suplogs', action='store_true', help='Perform suplogs installation only.')
    parser.add_argument('-t', '--test', dest='test', action='store_true', help='Perform test.')
    parser.add_argument('-n', '--notify', dest='notify', action='store_true', help='Perform hw-notify installation only.')

    args = parser.parse_args()

    if not any(vars(args).values()):
        printer.print_failure('Kindly provide a command line option for the script to execute.')
    else:
        if args.vm:
            package_manager.check_install_package(package_manager.packages, package_manager.python_packages)
            package_manager.download_ilorest_rpm(package_manager.ilorest_url, package_manager.ilorest_rpm_file)
            package_manager.install_ilorest()
            package_manager.install_suplogs(package_manager.suplogs)
            authorized.copy_keys()
            package_manager.hw_notify()

        if args.laptop:
            authorized.copy_keys()
            package_manager.hw_notify()

        if args.packages:
            package_manager.check_install_package(package_manager.packages, package_manager.python_packages)
            package_manager.download_ilorest_rpm(package_manager.ilorest_url, package_manager.ilorest_rpm_file)
            package_manager.install_ilorest()

        if args.suplogs:
            package_manager.check_install_package(package_manager.packages, package_manager.python_packages)
            package_manager.install_suplogs(package_manager.suplogs)

        if args.notify:
            package_manager.hw_notify()
