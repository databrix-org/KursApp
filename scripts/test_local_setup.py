"""Exercise local setup safety with fake CLIs; never starts Docker or accesses real data."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent.parent

class LocalSetupTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name)
        self.bin = self.repo / 'bin'
        self.bin.mkdir()
        (self.repo / 'scripts').mkdir()
        for script in ('preflight.sh', 'local.sh', 'docker-cli.sh'):
            shutil.copyfile(ROOT / 'scripts' / script, self.repo / 'scripts' / script)
        shutil.copyfile(ROOT / 'package.json', self.repo / 'package.json')
        (self.repo / 'compose.yaml').write_text('services: {}\n')
        (self.repo / '.env.example').write_text('DATABRIX_ENV=development\nDEMO_PASSWORD=fixture-only-password\n')
        for command in ('bash', 'dirname', 'sed', 'cat'):
            (self.bin / command).symlink_to(shutil.which(command))
        self.executable('git', '#!/bin/bash\nprintf "git version 2.50.0\\n"\n')
        self.executable('uname', '#!/bin/bash\nprintf "%s\\n" "${FAKE_OS:-Linux}"\n')
        self.executable('docker', '''#!/bin/bash
printf '%s\n' "$*" >> "$FAKE_LOG"
case "$*" in
  --version) echo 'Docker version 29.0.0, build fixture' ;;
  'compose version --short') echo "${FAKE_COMPOSE_VERSION:-5.6.1}" ;;
  'version --format '*) [[ "${FAKE_DAEMON_DOWN:-0}" == 1 ]] && exit 1; echo '29.0.0' ;;
  'context inspect '*) echo "${FAKE_ENDPOINT:-unix:///fixture/docker.sock}" ;;
  *django.conf*) [[ "${FAKE_GUARD_FAIL:-0}" == 1 ]] && { echo 'Refusing non-local configuration' >&2; exit 1; } ;;
esac
exit 0
''')
        self.env = dict(os.environ, PATH=str(self.bin), HOME=str(self.repo),
                        FAKE_LOG=str(self.repo / 'docker.log'), FAKE_OS='Linux')
        for name in ('DOCKER_HOST', 'DOCKER_CONTEXT'):
            self.env.pop(name, None)

    def executable(self, name, text):
        target = self.bin / name
        target.write_text(text)
        target.chmod(0o755)

    def run_script(self, script, *args, **env):
        return subprocess.run(['/bin/bash', str(self.repo / 'scripts' / script), *args],
            cwd=self.repo, env=self.env | env, text=True, capture_output=True)

    def calls(self):
        target = self.repo / 'docker.log'
        return target.read_text().splitlines() if target.exists() else []

    def test_docker_mode_works_without_host_development_tools_and_is_read_only(self):
        result = self.run_script('preflight.sh')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('Node is missing', result.stdout)
        self.assertIn('Preflight passed', result.stdout)
        self.assertFalse((self.repo / '.env').exists())
        self.assertFalse(any(' compose up ' in ' '+line for line in self.calls()))

    def test_development_mode_requires_missing_host_tools(self):
        result = self.run_script('preflight.sh', '--development')
        self.assertEqual(result.returncode, 1)
        self.assertIn('[FAIL] Node', result.stdout)
        self.assertIn('pnpm is missing', result.stdout)
        self.assertIn('uv is missing', result.stdout)

    def move_docker_outside_path(self):
        directory = self.repo / '.docker' / 'bin'
        directory.mkdir(parents=True)
        (self.bin / 'docker').rename(directory / 'docker')

    def test_macos_discovers_docker_outside_path_for_both_helpers(self):
        self.move_docker_outside_path()
        result = self.run_script('preflight.sh', FAKE_OS='Darwin')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('Docker found outside PATH', result.stdout)
        self.assertIn('Preflight passed', result.stdout)
        (self.repo / '.env').write_text('DATABRIX_ENV=development\n')
        result = self.run_script('local.sh', 'status', FAKE_OS='Darwin')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(any(line.endswith(' ps') for line in self.calls()))
        self.assertEqual(self.env['PATH'], str(self.bin))

    def test_discovered_cli_still_reports_stopped_engine(self):
        self.move_docker_outside_path()
        result = self.run_script('preflight.sh', FAKE_OS='Darwin', FAKE_DAEMON_DOWN='1')
        self.assertEqual(result.returncode, 1)
        self.assertIn('engine is unavailable', result.stdout)
        self.assertNotIn('[FAIL] Docker is missing', result.stdout)

    def test_unavailable_engine_and_old_compose_fail_preflight(self):
        result = self.run_script('preflight.sh', FAKE_DAEMON_DOWN='1', FAKE_COMPOSE_VERSION='2.20.0')
        self.assertEqual(result.returncode, 1)
        self.assertIn('engine is unavailable', result.stdout)
        self.assertIn('Compose 2.24.4+', result.stdout)

    def test_setup_preserves_existing_env_does_not_execute_it_and_orders_initialization(self):
        env_file = self.repo / '.env'
        marker = self.repo / 'must-not-exist'
        original = f'DATABRIX_ENV=development\nDEMO_PASSWORD=private-fixture-marker\nUNTRUSTED=$(touch {marker})\n'
        env_file.write_text(original)
        result = self.run_script('local.sh', 'setup')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(env_file.read_text(), original)
        self.assertFalse(marker.exists())
        self.assertNotIn('private-fixture-marker', result.stdout + result.stderr)
        calls = self.calls()
        guard = next(i for i, line in enumerate(calls) if 'django.conf' in line)
        migrate = next(i for i, line in enumerate(calls) if 'manage.py migrate ' in line)
        storage = next(i for i, line in enumerate(calls) if 'manage.py bootstrap_storage' in line)
        seed = next(i for i, line in enumerate(calls) if 'manage.py setup_dev_data' in line)
        self.assertLess(guard, migrate)
        self.assertLess(migrate, storage)
        self.assertLess(storage, seed)
        self.assertTrue(any('up -d --wait --wait-timeout 180' in line for line in calls))

    def test_new_env_is_private_and_rebuild_does_not_reseed(self):
        result = self.run_script('local.sh', 'setup')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.repo / '.env').stat().st_mode & 0o777, 0o600)
        (self.repo / 'docker.log').write_text('')
        result = self.run_script('local.sh', 'rebuild')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(any('manage.py migrate ' in line for line in self.calls()))
        self.assertFalse(any('setup_dev_' in line for line in self.calls()))

    def test_remote_endpoint_or_nonlocal_configuration_prevents_data_operations(self):
        result = self.run_script('local.sh', 'setup', FAKE_ENDPOINT='ssh://external.invalid')
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.repo / '.env').exists())
        result = self.run_script('local.sh', 'setup', FAKE_GUARD_FAIL='1')
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(any('manage.py' in line for line in self.calls()))

    def test_missing_docker_does_not_create_configuration(self):
        (self.bin / 'docker').unlink()
        result = self.run_script('local.sh', 'setup')
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.repo / '.env').exists())

if __name__ == '__main__':
    unittest.main()
