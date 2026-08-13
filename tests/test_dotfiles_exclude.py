import os
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


class DotfilesExcludeTest(unittest.TestCase):
    def test_excludes_relative_paths_and_name_patterns(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_path = Path(temporary_directory)
            source_repository = temporary_path / "source"
            destination_repository = temporary_path / "destination"
            source_repository.mkdir()

            for relative_path in (
                ".zshrc",
                ".aws/config",
                ".claude/scripts/statusline.sh",
                ".claude/worktrees/child.txt",
                ".superpowers/config.yml",
                "nested/.gitignore",
            ):
                file_path = source_repository / relative_path
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text("content\n")

            self.run_command(["git", "init"], source_repository)
            self.run_command(["git", "add", "."], source_repository)
            self.run_command(
                [
                    "git",
                    "-c",
                    "user.email=test@example.com",
                    "-c",
                    "user.name=Test User",
                    "commit",
                    "-m",
                    "Initial fixture",
                ],
                source_repository,
            )

            playbook_path = temporary_path / "playbook.yaml"
            playbook_path.write_text(
                textwrap.dedent(
                    f"""\
                    ---
                    - hosts: localhost
                      connection: local
                      gather_facts: false
                      vars:
                        dotfiles_repo: {source_repository}
                        dotfiles_repo_version: HEAD
                        dotfiles_repo_local_destination: {destination_repository}
                        dotfiles_exclude:
                          - .aws/config
                          - .claude/worktrees
                          - .superpowers
                          - .gitignore
                        dotfiles_executable_dirs:
                          - .claude/scripts
                      roles:
                        - dotfiles
                      tasks:
                        - ansible.builtin.assert:
                            that:
                              - "'.zshrc' in dotfiles_files"
                              - "'.aws/config' not in dotfiles_files"
                              - "'.claude/worktrees/child.txt' not in dotfiles_files"
                              - "'.superpowers/config.yml' not in dotfiles_files"
                              - "'nested/.gitignore' not in dotfiles_files"
                    """
                )
            )

            environment = os.environ | {"ANSIBLE_ROLES_PATH": str(REPOSITORY_ROOT / "roles")}
            result = subprocess.run(
                ["ansible-playbook", str(playbook_path)],
                cwd=REPOSITORY_ROOT,
                env=environment,
                text=True,
                capture_output=True,
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def run_command(self, command, directory):
        subprocess.run(command, cwd=directory, check=True, capture_output=True)


if __name__ == "__main__":
    unittest.main()
