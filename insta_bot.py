import json
import random
import time
import sys
from instagrapi import Client

# Load credentials from config file
try:
    with open("config.json", "r") as f:
        CONFIG = json.load(f)
except FileNotFoundError:
    print("❌ 'config.json' not found. Please ensure your secrets are loaded correctly.")
    sys.exit(1)

# Instagram accounts
ACCOUNTS = CONFIG["accounts"]

# Follow sources for each account
FOLLOW_SOURCES = CONFIG["follow_sources"]

# Load followed users to prevent re-following
try:
    with open("followed_users.json", "r") as f:
        FOLLOWED_USERS = json.load(f)
except FileNotFoundError:
    FOLLOWED_USERS = {account: [] for account in ACCOUNTS}

# Clients dictionary for logged-in sessions
clients = {}

def login_instagram(account_name):
    """Logs into a given Instagram account using instagrapi."""
    cl = Client()
    creds = ACCOUNTS[account_name]
    cl.login(creds["username"], creds["password"])
    clients[account_name] = cl
    print(f"✅ Logged in as {account_name}")

def save_followed_users():
    """Saves updated list of followed users to a JSON file."""
    with open("followed_users.json", "w") as f:
        json.dump(FOLLOWED_USERS, f, indent=4)

def follow_unfollow(account_name, max_follows=40):
    """
    Follows a limited number of new users from random source accounts.
    Then unfollows oldest follows when threshold is exceeded.
    """
    # 1) Ensure logged in
    if account_name not in clients:
        login_instagram(account_name)
    cl = clients[account_name]

    print(f"⚡ Running follow/unfollow for {account_name}")

    # 2) Pick a random source account
    source_account = random.choice(FOLLOW_SOURCES[account_name])
    print(f"📌 Fetching followers from @{source_account}")

    # 3) Fetch up to 100 followers from source
    user_id = cl.user_id_from_username(source_account)
    followers = cl.user_followers(user_id, amount=100)

    # 4) Filter out already-followed
    new_followers = [uid for uid in followers.keys() if uid not in FOLLOWED_USERS[account_name]]

    if not new_followers:
        print(f"⚠️ No new users to follow for {account_name}")
        return

    # 5) Follow up to `max_follows` new users
    to_follow = random.sample(new_followers, min(max_follows, len(new_followers)))
    for user in to_follow:
        try:
            cl.user_follow(user)
            FOLLOWED_USERS[account_name].append(user)
            print(f"✅ Followed {user}")
            # Short random delay between 0.5 and 1.5 seconds
            time.sleep(random.uniform(0.5, 1.5))
        except Exception as e:
            print(f"❌ Error following {user}: {e}")

    # 6) Save after following
    save_followed_users()

    # 7) Unfollow oldest if list is too long
    if len(FOLLOWED_USERS[account_name]) > 200:
        to_unfollow = FOLLOWED_USERS[account_name][:50]
        for user in to_unfollow:
            try:
                cl.user_unfollow(user)
                FOLLOWED_USERS[account_name].remove(user)
                print(f"🚀 Unfollowed {user}")
                time.sleep(random.uniform(0.5, 1.5))
            except Exception as e:
                print(f"❌ Error unfollowing {user}: {e}")

        save_followed_users()

def main():
    """Executes follow/unfollow once for each account, then exits."""
    # Adjust max_follows if you want a different daily total
    for account_name in ACCOUNTS:
        follow_unfollow(account_name, max_follows=40)

if __name__ == "__main__":
    main()
