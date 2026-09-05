import os
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


class DotfilesLocalModificationsTest(unittest.TestCase):
    def test_local_modifications_are_preserved_while_pulling_upstream_changes(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_path = Path(temporary_directory)
            source_repository = temporary_path / "source"
            destination_repository = temporary_path / "destination"
            source_repository.mkdir()

            (source_repository / ".zshrc").write_text("upstream line\n")
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

            self.run_command(
                ["git", "clone", str(source_repository), str(destination_repository)],
                temporary_path,
            )

            # Upstream gains a new commit after the clone.
            (source_repository / "new_file.txt").write_text("added later\n")
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
                    "Add file after clone",
                ],
                source_repository,
            )

            # Destination has an uncommitted local edit, unrelated to the upstream change.
            with (destination_repository / ".zshrc").open("a") as handle:
                handle.write("local wip line\n")

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
                        dotfiles_repo_version: main
                        dotfiles_repo_local_destination: {destination_repository}
                        dotfiles_exclude: []
                        dotfiles_executable_dirs: []
                      roles:
                        - dotfiles
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

            zshrc_content = (destination_repository / ".zshrc").read_text()
            self.assertIn("local wip line", zshrc_content, "local edit must be preserved")

            self.assertTrue(
                (destination_repository / "new_file.txt").exists(),
                "upstream commit must be pulled",
            )

    def test_module_defaults_prevent_a_dependent_roles_git_task_from_failing(self):
        # geerlingguy.dotfiles runs its own independent ansible.builtin.git
        # clone/update against the same destination as roles/dotfiles. This
        # simulates that task (short "git" module name, same params) to
        # verify playbook.yaml's module_defaults keeps it from failing on
        # local modifications too, once roles/dotfiles has already synced.
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_path = Path(temporary_directory)
            source_repository = temporary_path / "source"
            destination_repository = temporary_path / "destination"
            source_repository.mkdir()

            (source_repository / ".zshrc").write_text("upstream line\n")
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

            self.run_command(
                ["git", "clone", str(source_repository), str(destination_repository)],
                temporary_path,
            )

            with (destination_repository / ".zshrc").open("a") as handle:
                handle.write("local wip line\n")

            playbook_path = temporary_path / "playbook.yaml"
            playbook_path.write_text(
                textwrap.dedent(
                    f"""\
                    ---
                    - hosts: localhost
                      connection: local
                      gather_facts: false
                      module_defaults:
                        ansible.builtin.git:
                          update: false
                      vars:
                        dotfiles_repo: {source_repository}
                        dotfiles_repo_version: main
                        dotfiles_repo_local_destination: {destination_repository}
                      tasks:
                        - name: Simulate a dependent role's own clone/update task
                          git:
                            repo: "{{{{ dotfiles_repo }}}}"
                            dest: "{{{{ dotfiles_repo_local_destination }}}}"
                            version: "{{{{ dotfiles_repo_version }}}}"
                    """
                )
            )

            result = subprocess.run(
                ["ansible-playbook", str(playbook_path)],
                cwd=REPOSITORY_ROOT,
                text=True,
                capture_output=True,
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn(
                "local wip line",
                (destination_repository / ".zshrc").read_text(),
            )

    def run_command(self, command, directory):
        subprocess.run(command, cwd=directory, check=True, capture_output=True)


if __name__ == "__main__":
    unittest.main()
