import os
import git
import re
import argparse
import hashlib

# Colors
BLUE = "\33[94m"
END = "\033[0m"

# Parse command-line arguments
parser = argparse.ArgumentParser(description="Search for files in a Git repository and copy them to an output folder.")
parser.add_argument("-r", "--repository", required=True, help="Path to the Git repository")
parser.add_argument("-f", "--file", help="File containing patterns to search for (default: .gitignore in the repository folder)")
parser.add_argument("-o", "--output", default="extracted", help="Output folder to copy matched files to (default: extracted)")
parser.add_argument("-a", "--all", action="store_true", default=False, help="Restore all deleted files. Ignore --file")
parser.add_argument("-v", "--verbose", action="store_true", default=False, help="Restore all deleted files. Ignore --file")
args = parser.parse_args()

# Set the repository path, filename, output folder, and number of threads
repository_path = args.repository
file_path = args.file or os.path.join(repository_path, ".gitignore")
output_folder = args.output
verbose = args.verbose
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

def generate_report(dct):
    extension_counts = {}
    total_restore_files = len(dct)

    for file_path in copied_files:
        
        # Split the file path into components
        components = file_path.split("/")
        file_name = components[-1]
        
        # Handle hidden files
        if file_name.startswith("."):
            file_extension = file_name[1:]
        else:
            file_name, file_extension = file_name.rsplit(".", 1) if "." in file_name else (file_name, file_name)
        
        # Update the extension count
        extension_counts[file_extension.upper()] = extension_counts.get(file_extension.upper(), 0) + 1

    # Sort the extensions by the number of files in each group (descending order)
    sorted_extensions = sorted(extension_counts.items(), key=lambda x: x[1], reverse=True)

    # Generate the report
    report = f"{BLUE}Restored files: {total_restore_files}{END}\n"
    report += f"{BLUE}Group by extensions:{END}\n"

    for extension, count in sorted_extensions:
        report += f"  {BLUE}{count}{END} files{' '*(8-len(str(count)))}{extension}\n"

    print(f"{report}")
    print(f"{BLUE}Done.{END}")
    return

        
def process_commit(commit, patterns, output_folder):
    """Process a single commit to check for file matches and copy them to the output folder."""
    commit_folder = os.path.join(output_folder, commit.hexsha[:8])
    files_found_in_commit = False
    for parent in commit.parents:
        diff = parent.diff(commit)
        for file_d in diff:
            try:
                if file_d.deleted_file:
                    if not args.all:
                        if not check_match(patterns, file_d.a_path):
                            continue
                    files_found_in_commit = True
                    if file_d.a_path not in copied_files:
                        if verbose:
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
            except Exception as exc:
                print(f"{exc}")
    return files_found_in_commit

def process_line(repo_path, patterns, output_folder):
    repo = git.Repo(repo_path)
    found_files = False
    for commit in repo.iter_commits('--all'):
        if process_commit(commit, patterns, output_folder):
            found_files = True
    if not found_files:
        print(f"{BLUE}No files found.{END}")
    else:
        generate_report(copied_files)
        with open(f"{output_folder}/gittrash.log", "w") as file:
            for file_path in copied_files.keys():
                file.write(file_path + "\n")

def banner():
    banner = f"""
    {BLUE}\n
 __    ___          
/ _ .|_ | _ _  _|_  
\__)||_ || (_|_)| )\n{END}
    {BLUE}Created by{END}: @Sheryx00
    {BLUE}Github{END}: https://github.com/Sheryx00/GitTrash\n"""
    return banner

if __name__ == "__main__":
    print(banner())
    if not verbose:
        print(f"Working quietly. Wait for report.")
    repo = git.Repo(repository_path)
    os.makedirs(output_folder, exist_ok=True)
    gitignore_patterns = sanitize_grep_file(file_path)
    regex_patterns = convert_gitignore_to_regex(gitignore_patterns)
    abs_repository_path = os.path.abspath(repository_path)
    process_line(abs_repository_path, regex_patterns, output_folder)
