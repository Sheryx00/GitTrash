import os
import git
import fnmatch
import argparse

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

def sanitize_grep_file(file_path):
    """Sanitize the grep file by removing empty lines and lines starting with #."""
    sanitized_lines = []
    with open(file_path, "r") as file:
        for line in file:
            line = line.strip()
            if line and not line.startswith("#"):
                sanitized_lines.append(line)
    return sanitized_lines

def check_match(patterns, string):
    for pattern in patterns:
        if fnmatch.fnmatch(str(string), pattern):
            return True
    return False

def process_commit(commit, patterns, output_folder):
    """Process a single commit to check for file matches and copy them to the output folder."""
    commit_folder = os.path.join(output_folder, commit.hexsha[:8])
    files_found_in_commit = False
    for parent in commit.parents:
        diff = parent.diff(commit)
        for file_d in diff:
            if check_match(patterns, file_d):
                print(f"{commit.hexsha} {file_d.a_path}")
                files_found_in_commit = True
                # Copy the file to the output folder
                if file_d.a_path in parent.tree:
                    print(f"{commit.hexsha} {file_d.a_path}")
                    os.makedirs(commit_folder, exist_ok=True)
                    with open(os.path.join(commit_folder, file_d.a_path.replace('/','_')), 'wb') as f:
                        blob = parent.tree[file_d.a_path]
                        f.write(blob.data_stream.read())
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
    patterns = sanitize_grep_file(file_path)
    abs_repository_path = os.path.abspath(repository_path)
    process_line(abs_repository_path, patterns, output_folder)
