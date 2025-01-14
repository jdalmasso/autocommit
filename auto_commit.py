import os
import random
import json
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
COMMIT_TIMES_FILE = os.path.join(REPO_PATH, "commit_times.json")
LOG_FILE = os.path.join(REPO_PATH, "commit_log.txt")
ERROR_LOG_FILE = os.path.join(REPO_PATH, "error_log.txt")
TIMEZONE = pytz.timezone("US/Eastern")

# Logging Setup
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
)

# Error Logging
error_logger = logging.getLogger("error_logger")
error_logger.addHandler(logging.FileHandler(ERROR_LOG_FILE))

def select_commit_times(working_hours, num_commits):
    """Generate random commit times for the day."""
    start, end = working_hours
    start_time = datetime.combine(datetime.now(TIMEZONE).date(), datetime.strptime(start, "%H:%M").time()).astimezone(TIMEZONE)
    end_time = datetime.combine(datetime.now(TIMEZONE).date(), datetime.strptime(end, "%H:%M").time()).astimezone(TIMEZONE)

    commit_times = []
    for _ in range(num_commits):
        delta = (end_time - start_time).total_seconds()
        random_offset = random.randint(0, int(delta))
        commit_time = start_time + timedelta(seconds=random_offset)
        commit_times.append(commit_time.isoformat())

    return sorted(commit_times)

def save_commit_times(commit_times):
    """Save commit times to a JSON file."""
    with open(COMMIT_TIMES_FILE, "w") as file:
        json.dump(commit_times, file)

def load_commit_times():
    """Load commit times from the JSON file."""
    if os.path.exists(COMMIT_TIMES_FILE):
        with open(COMMIT_TIMES_FILE, "r") as file:
            return json.load(file)
    return []

def update_counter():
    """Update the counter file."""
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
    """Commit changes to the repository."""
    try:
        repo.git.add(COUNTER_FILE, LOG_FILE, ERROR_LOG_FILE)
        commit_message = f"Updated counter from {counter_before} to {counter_after}"
        repo.git.commit(m=commit_message)
        return commit_message
    except Exception as e:
        error_logger.error(f"Commit failed: {e}")
        raise

def push_changes(repo):
    """Push committed changes to the remote repository."""
    try:
        repo.git.push()
    except Exception as e:
        error_logger.error(f"Push failed: {e}")
        raise

def main():
    """Main script logic."""
    try:
        repo = Repo(REPO_PATH)

        # Determine if we're setting up the day or executing a commit
        now = datetime.now(TIMEZONE)
        commit_times = load_commit_times()

        if not commit_times:
            # Setup for the day
            working_hours = ["09:00", "19:00"] if now.weekday() < 6 else ["11:00", "16:00"]
            num_commits = 1 if now.weekday() == 6 else random.randint(1, 10)
            commit_times = select_commit_times(working_hours, num_commits)
            save_commit_times(commit_times)
            logging.info(f"Commit times for the day: {commit_times}")
        else:
            # Check if it's time to commit
            next_commit_time = datetime.fromisoformat(commit_times[0]).astimezone(TIMEZONE)
            if now >= next_commit_time:
                counter_before, counter_after = update_counter()
                commit_message = make_commit(repo, counter_before, counter_after)
                push_changes(repo)

                # Log the commit
                logging.info(
                    f"Commit executed at {now}: {commit_message} (Remaining commit times: {commit_times[1:]})"
                )

                # Remove the executed time and save
                commit_times.pop(0)
                save_commit_times(commit_times)
    except Exception as e:
        error_logger.error(f"Script error: {e}")

if __name__ == "__main__":
    main()
