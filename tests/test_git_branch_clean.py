import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPOSITORY_ROOT / "roles" / "scripts" / "files" / "git-branch-clean.sh"


class GitBranchCleanTest(unittest.TestCase):
    def test_processes_repositories_in_dot_directories(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_path = Path(temporary_directory)
            origin_repository = temporary_path / "origin.git"
            seed_repository = temporary_path / "seed"
            workspace = temporary_path / "workspace"
            workspace.mkdir()

            self.run_command(["git", "init", "--bare", "-b", "main", str(origin_repository)], temporary_path)
            self.run_command(["git", "clone", str(origin_repository), str(seed_repository)], temporary_path)
            self.run_command(
                [
                    "git",
                    "-c",
                    "user.email=test@example.com",
                    "-c",
                    "user.name=Test User",
                    "commit",
                    "--allow-empty",
                    "-m",
                    "Initial fixture",
                ],
                seed_repository,
            )
            self.run_command(["git", "push", "origin", "main"], seed_repository)

            for name in (".dotrepo", "plainrepo"):
                self.run_command(["git", "clone", str(origin_repository), str(workspace / name)], temporary_path)

            script = workspace / SCRIPT_PATH.name
            shutil.copy(SCRIPT_PATH, script)
            result = subprocess.run(["bash", str(script)], text=True, capture_output=True)

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            processed = result.stdout.splitlines()
            self.assertIn(str(workspace / ".dotrepo"), processed)
            self.assertIn(str(workspace / "plainrepo"), processed)

    def run_command(self, command, directory):
        subprocess.run(command, cwd=directory, check=True, capture_output=True)


if __name__ == "__main__":
    unittest.main()
