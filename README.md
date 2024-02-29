# GitTrash

GitTrash will allow you to search for files that have been deleted in the repository. It is extremely useful for finding files that have been excluded in .gitignore but still exist in the history.

I coded it for pentesters and bug hunters. But it can also be useful for developers.

### Installation

    Clone the repository:
    > git clone git@github.com:Sheryx00/GitTrash.git

    Install Dependencies 
    > run pip install -r requirements.txt


### USAGE
> python gittrash.py -r /path/to/repository -o output_folder


```
python3 gittrash.py -h
usage: gittrash.py [-h] -r REPOSITORY [-f FILE] [-o OUTPUT]

Search for files in a Git repository and copy them to an output folder.

options:
  -h, --help            show this help message and exit
  -r REPOSITORY, --repository REPOSITORY
                        Path to the Git repository
  -f FILE, --file FILE  File containing patterns to search for (default:
                        .gitignore in the repository folder)
  -o OUTPUT, --output OUTPUT
                        Output folder to copy matched files to (default:
                        extracted)
```