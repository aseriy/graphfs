import argparse
from git import Repo, Commit
import sys
import os
from pathlib import Path
from shutil import rmtree, copytree
import json
from binstore.upload import upload_dir as upload_commit


def clone(url, path):
  local_repo_path = None

  # Check if the data path exists and not a file
  # If it doesn't exist, create it
  if os.path.exists(path) and not os.path.isdir(path):
    sys.exit("{} exists and not a directory. Exiting...".format(path))

  if os.path.exists(path):
     print("Repository {} exists. Removing...".format(path))
     rmtree(path)


  os.makedirs(path)

  local_repo_path = os.path.join(path, Path(url).stem)
  Repo.clone_from(url, local_repo_path)

  return local_repo_path


# Declaring the ignore function
def ignore_dot_git(path, names):
  return [name for name in names if name == '.git']


def checkout(repo, commit_id):
  print("Checking out commit {}".format(commit_id))

  # blast any current changes
  repo.git.reset('--hard')
  # remove any extra non-tracked files (.pyc, etc)
  repo.git.clean('-xdf')
  repo.git.checkout(commit_id)

  # copy the content of the commit to a temp directory
  commit_path = os.path.join(
    os.path.dirname(os.path.dirname(repo.working_tree_dir)),
    'tmp', str(commit_id))
  copytree(repo.working_tree_dir, commit_path, ignore = ignore_dot_git)

  return commit_path



def commit_tracker_read(path):
  commits_done = []

  # Check if the commit tracker file exists.
  # Create if doesn't exist.
  if not os.path.isdir(os.path.dirname(path)):
    os.makedirs(os.path.dirname(path))

  if not os.path.isfile(path):
    f = open(path, "w")
    f.write(json.dumps(commits_done, indent=4))
    f.close()

  else:
    with open(path) as f:
      commits_done = json.loads(f.read())

  return { c:True for c in commits_done }



def commit_tracker_write(path, data):
  commits_done = [c for c in data.keys()]
  commits_done = json.dumps(commits_done, indent=4)

  # Check if the commit tracker file exists.
  # Create if doesn't exist.
  if not os.path.isdir(os.path.dirname(path)):
    os.makedirs(os.path.dirname(path))

  f = open(path, "w")
  f.write(commits_done)
  f.close()

  return None


#
# Main
#
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
            prog = __file__,
            description = "Copy Git repo content, each commit into a separate directory."
        )

    parser.add_argument("-r", "--repo", type=str, required=True,
                        help="Remote Git repository URL."
                    )
    parser.add_argument("-d", "--data", type=str, required=True,
                        help="Directory path to store downloaded data."
                    )
    parser.add_argument("-m", "--max", type=int, required=False, default=None,
                        help="Maximum number of commits to process. Default: all."
                    )

    args, unknown = parser.parse_known_args()

    repo_url = args.repo
    data_dir = args.data
    max_commits = args.max
    commit_tracker = os.path.join(os.path.dirname(__file__),'.{}'.format(Path(__file__).stem))

    # repo_path = clone(repo_url, os.path.join(data_dir, 'git'))
    repo_path = os.path.join(data_dir, 'git', Path(repo_url).stem)

    repo = Repo(repo_path)

    all_commits = list()

    remote_refs = repo.remote().refs
    for ref in remote_refs:
      print("REF: ", ref.name)
      branch = ref.name
      # branch = ref.name.lstrip('origin/')
      print("BRANCH: ", branch)

      commits = list(repo.iter_commits(branch))
      for commit in commits:
        all_commits.append(commit)


    print("Commits: ", len(all_commits))
    all_commits = list(set(all_commits))
    print("Commits unique: ", len(all_commits))
    print("Commit tracker file: ", commit_tracker)

    
    commits_done = commit_tracker_read(commit_tracker)
    print(json.dumps(commits_done, indent=4))


    commits_left = max_commits
    for commit in all_commits:
      if commits_left > 0:
        if not commit in commits_done:
          commit_path = checkout(repo, commit)

          # Upload the commit to GraphFS
          print("Dest: ", os.path.basename(repo.working_dir))
          print("Src:  ", commit_path)
          upload_commit(
            os.path.basename(repo.working_dir),
            commit_path
          )

          # Clean up
          rmtree(commit_path)

          commits_done[str(commit)] = True
          commits_left -= 1
  
          commit_tracker_write(commit_tracker, commits_done)

    exit(0)


