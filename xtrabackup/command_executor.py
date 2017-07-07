import subprocess
from xtrabackup.exception import ProcessError


class CommandExecutor:

    def __init__(self, output_file_path):
        self.output_file_path = output_file_path

    def exec_command(self, command):
        with open(self.output_file_path, 'a+') as error_file:
            process = subprocess.Popen(command, stdout=error_file,
                                       stderr=subprocess.STDOUT)
            process.communicate()
            if process.returncode != 0:
                raise ProcessError(command, process.returncode)

    def run_bash(self, command):
        with open(self.output_file_path, 'a+') as error_file:
            process = subprocess.run(['bash', '-c', command], stdout=error_file, stderr=subprocess.STDOUT)
            if process.returncode != 0:
                raise ProcessError(command, process.returncode)

    def exec_filesystem_backup(self, user, password,
                               threads, backup_directory, host, datadir):
        command = [
            'xtrabackup',
            # '--defaults-file=' + datadir + '/my.ini',
            '--backup',
            '--user=' + user,
            '--parallel=' + threads,
            # '--no-lock',
            # '--no-timestamp',
            '--target-dir=' + backup_directory]
        if password:
            command.append('--password=' + password)
        if host:
            command.append('--host=' + host)
        if datadir:
            command.append('--datadir=' + datadir)
        self.exec_command(command)

    def exec_incremental_backup(self, user, password,
                                threads, lsn, backup_directory, host, datadir):
        command = [
            'xtrabackup',
            '--backup',
            '--user=' + user,
            '--parallel=' + threads,
            '--incremental',
            '--incremental-lsn=' + lsn,
            # '--no-lock',
            # '--no-timestamp',
            '--incremental-force-scan',
            '--target-dir=' + backup_directory]
        if password:
            command.append('--password=' + password)
        if host:
            command.append('--host=' + host)
        if datadir:
            command.append('--datadir=' + datadir)
        self.exec_command(command)

    def exec_backup_preparation(self, backup_directory, redo_logs):
        command = [
            'xtrabackup',
            '--prepare',
            '--apply-log-only',
            '--target-dir=' + backup_directory]
        # if redo_logs:
        #     command.append('--redo-only')
        self.exec_command(command)

    def exec_incremental_preparation(self, backup_directory,
                                     incremental_directory):
        command = [
            'xtrabackup',
            '--prepare',
            '--apply-log-only',
            '--incremental-dir=' + incremental_directory,
            '--target-dir=' + backup_directory]
        self.exec_command(command)

    def exec_manage_service(self, service_name, action):
        command = ['service', service_name, action]
        self.exec_command(command)

    def exec_chown(self, user, group, directory_path):
        command = ['/bin/chown', '-R', user + ':' + group, directory_path]
        self.exec_command(command)

    def create_archive(self, directory, archive_path, compress, compression_tool, encryption_key):
        if compression_tool == 'gz':
            if compress:
                tar_options = 'cpvzf'
            else:
                tar_options = 'cpvf'

            command = [
                'tar',
                tar_options,
                archive_path,
                '-C',
                directory, '.']
            self.exec_command(command)
        elif compression_tool == '7z':
            command = 'tar cpvf - -C %s . | 7z a -si %s -mhe -mx=9' % (directory, archive_path)

            if encryption_key:
                command += ' -p%s' % (encryption_key)
            
            self.run_bash(command)

    def extract_archive(self, archive_path, destination_path, compressed):
        if compressed:
            tar_options = 'xpvzf'
        else:
            tar_options = 'xpvf'
        command = [
            'tar',
            tar_options,
            archive_path,
            '-C',
            destination_path]
        self.exec_command(command)
