import os
import git
import re
import argparse
import hashlib

# Parse command-line arguments
parser = argparse.ArgumentParser(description="Search for files in a Git repository and copy them to an output folder.")
parser.add_argument("-r", "--repository", required=True, help="Path to the Git repository")
parser.add_argument("-f", "--file", help="File containing patterns to search for (default: .gitignore in the repository folder)")
parser.add_argument("-o", "--output", default="extracted", help="Output folder to copy matched files to (default: extracted)")
args = parser.parse_args()

# Set the repository path, filename, output folder, and number of threads
repository_path = args.repository
file_path = args.file or os.path.join(repository_path, ".gitignore")
output_folder = args.output
copied_files = {}  # Keep track of copied files and their hashes

def sanitize_grep_file(file_path):
    """Sanitize the grep file by removing empty lines and lines starting with #."""
    sanitized_lines = []
    with open(file_path, "r") as file:
        for line in file:
            line = line.strip()
            if line and not line.startswith(("#","!")):
                sanitized_lines.append(line)
    return sanitized_lines

def convert_gitignore_to_regex(gitignore_patterns):
    """Convert Gitignore patterns to regex patterns."""
    regex_patterns = []
    for pattern in gitignore_patterns:
        regex_pattern = pattern.replace('.', r'\.').replace('*', '.*').replace('?', '.')
        regex_patterns.append(regex_pattern)
    return regex_patterns

def check_match(patterns, string):
    for pattern in patterns:
        if re.match(pattern, string):
            return True
    return False

def get_sha256(data):
    """Calculate the SHA-256 hash of data."""
    sha256 = hashlib.sha256()
    sha256.update(data)
    return sha256.hexdigest()

def process_commit(commit, patterns, output_folder):
    """Process a single commit to check for file matches and copy them to the output folder."""
    commit_folder = os.path.join(output_folder, commit.hexsha[:8])
    files_found_in_commit = False
    for parent in commit.iter_parents():
        diff = parent.diff(commit)
        for file_d in diff:
            if check_match(patterns, file_d.a_path):
                files_found_in_commit = True
                # Copy the file to the output folder if it hasn't been copied before
                if file_d.deleted_file:
                    if file_d.a_path not in copied_files:
                        print(f"{commit.hexsha[:8]}/{file_d.a_path.replace('/', '_')}")
                        os.makedirs(commit_folder, exist_ok=True)
                        file_path = os.path.join(commit_folder, file_d.a_path.replace('/', '_'))
                        copied_files[file_d.a_path] = [get_sha256(file_d.a_blob.data_stream.read())]
                        # Find the file in the parent commit
                        for ancestor_file in parent.tree.traverse():
                            if ancestor_file.path == file_d.a_path:
                                with open(file_path, 'wb') as f:
                                    f.write(ancestor_file.data_stream.read())
                                break
                    else:
                        sha256 = get_sha256(file_d.a_blob.data_stream.read())
                        if sha256 not in copied_files[file_d.a_path]:
                            copied_files[file_d.a_path].append(sha256)
    return files_found_in_commit

def process_line(repo_path, patterns, output_folder):
    """Process a single line to check for file matches in all commits."""
    repo = git.Repo(repo_path)
    found_files = False
    for commit in repo.iter_commits('--all'):
        if process_commit(commit, patterns, output_folder):
            found_files = True
    if not found_files:
        print(f"No files found.")

if __name__ == "__main__":
    repo = git.Repo(repository_path)
    os.makedirs(output_folder, exist_ok=True)
    gitignore_patterns = sanitize_grep_file(file_path)
    regex_patterns = convert_gitignore_to_regex(gitignore_patterns)
    abs_repository_path = os.path.abspath(repository_path)
    process_line(abs_repository_path, regex_patterns, output_folder)
