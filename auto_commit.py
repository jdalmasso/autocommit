import os
import random
import time
from datetime import datetime, timedelta
from git import Repo
import pytz
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get the repository path from the .env file
REPO_PATH = os.getenv("REPO_PATH")
if not REPO_PATH:
    raise ValueError("REPO_PATH not set in .env file")

# Constants
COUNTER_FILE = os.path.join(REPO_PATH, "counter.txt")
LOG_FILE = os.path.join(REPO_PATH, "commit_log.txt")
ERROR_LOG_FILE = os.path.join(REPO_PATH, "error_log.txt")
CONFIG_FILE = os.path.join(REPO_PATH, "config.json")

# Timezone Configuration
ET = pytz.timezone("US/Eastern")

# Logging Setup
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
)

# Error Logging
error_logger = logging.getLogger("error_logger")
error_logger.addHandler(logging.FileHandler(ERROR_LOG_FILE))


def load_config():
    try:
        with open(CONFIG_FILE, "r") as file:
            return json.load(file)
    except Exception as e:
        error_logger.error(f"Error loading config: {e}")
        raise


def get_commit_times(working_hours, num_commits, is_sunday):
    start, end = working_hours
    commit_times = []

    if is_sunday:
        start_time = datetime.combine(datetime.today(), datetime.strptime("11:00", "%H:%M").time()).astimezone(ET)
        end_time = datetime.combine(datetime.today(), datetime.strptime("16:00", "%H:%M").time()).astimezone(ET)
        commit_times.append(random_time_between(start_time, end_time))
    else:
        start_time = datetime.combine(datetime.today(), datetime.strptime(start, "%H:%M").time()).astimezone(ET)
        end_time = datetime.combine(datetime.today(), datetime.strptime(end, "%H:%M").time()).astimezone(ET)
        intervals = sorted([random_time_between(start_time, end_time) for _ in range(num_commits)])
        commit_times = sorted(intervals)

    return commit_times


def random_time_between(start, end):
    delta = end - start
    random_seconds = random.randint(0, int(delta.total_seconds()))
    return start + timedelta(seconds=random_seconds)


def update_counter():
    if not os.path.exists(COUNTER_FILE):
        with open(COUNTER_FILE, "w") as file:
            file.write("0")

    with open(COUNTER_FILE, "r") as file:
        counter = int(file.read().strip())

    increment = random.randint(1, 100)
    new_counter = counter + increment

    with open(COUNTER_FILE, "w") as file:
        file.write(str(new_counter))

    return counter, new_counter


def make_commit(repo, counter_before, counter_after):
    try:
        repo.git.add(COUNTER_FILE)
        commit_message = f"Updated counter from {counter_before} to {counter_after}"
        repo.git.commit(m=commit_message)
        return commit_message
    except Exception as e:
        error_logger.error(f"Commit failed: {e}")
        raise


def push_changes(repo):
    try:
        repo.git.push()
    except Exception as e:
        error_logger.error(f"Push failed: {e}")
        raise


def main():
    try:
        # Load Config
        config = load_config()
        working_hours = config["working_hours"]
        max_commits = config["max_commits"]

        # Check if Sunday
        today = datetime.now(ET).date()
        is_sunday = today.weekday() == 6

        # Determine Number of Commits
        num_commits = 1 if is_sunday else random.randint(1, max_commits)

        # Determine Commit Times
        commit_times = get_commit_times(working_hours, num_commits, is_sunday)

        # Repository Setup
        repo = Repo(REPO_PATH)
        if repo.is_dirty(untracked_files=True):
            error_logger.error("Repository has untracked or dirty files.")
            return

        # Process Commits
        for i, commit_time in enumerate(commit_times):
            time_until_commit = (commit_time - datetime.now(ET)).total_seconds()
            if time_until_commit > 0:
                time.sleep(time_until_commit)

            counter_before, counter_after = update_counter()
            commit_message = make_commit(repo, counter_before, counter_after)

            # Log Commit Details
            logging.info(
                f"Commit {i+1}/{num_commits} - Message: {commit_message}, Time: {commit_time.strftime('%Y-%m-%d %H:%M:%S')}"
            )

        # Push Changes
        push_changes(repo)

    except Exception as e:
        error_logger.error(f"Script error: {e}")


if __name__ == "__main__":
    main()
