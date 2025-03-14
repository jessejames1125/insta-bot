import json
import random
import time
import schedule
from instagrapi import Client
from datetime import datetime, timedelta

# Load credentials from config file
with open("config.json", "r") as f:
    CONFIG = json.load(f)

# Instagram accounts
ACCOUNTS = CONFIG["accounts"]

# Follow sources for each account
FOLLOW_SOURCES = CONFIG["follow_sources"]

# Load followed users to prevent re-following
try:
    with open("followed_users.json", "r") as f:
        FOLLOWED_USERS = json.load(f)
except FileNotFoundError:
    FOLLOWED_USERS = {"ig_1": [], "ig_2": []}

# Clients dictionary for logged-in sessions
clients = {}

# Login function
def login_instagram(account_name):
    cl = Client()
    creds = ACCOUNTS[account_name]
    cl.login(creds["username"], creds["password"])
    clients[account_name] = cl
    print(f"✅ Logged in as {account_name}")

# Function to avoid refollowing users
def save_followed_users():
    with open("followed_users.json", "w") as f:
        json.dump(FOLLOWED_USERS, f, indent=4)

# Follow and unfollow logic
def follow_unfollow(account_name):
    cl = clients.get(account_name)
    if not cl:
        login_instagram(account_name)
        cl = clients[account_name]

    print(f"⚡ Running follow/unfollow for {account_name}")

    # Select a random source account
    source_account = random.choice(FOLLOW_SOURCES[account_name])
    print(f"📌 Fetching followers from @{source_account}")

    # Get followers from source account
    user_id = cl.user_id_from_username(source_account)
    followers = cl.user_followers(user_id, amount=100)

    # Filter out already-followed users
    new_followers = [uid for uid in followers.keys() if uid not in FOLLOWED_USERS[account_name]]

    if not new_followers:
        print(f"⚠️ No new users to follow for {account_name}. Try different sources.")
        return

    # Select up to 50 new users to follow
    to_follow = random.sample(new_followers, min(50, len(new_followers)))

    for user in to_follow:
        try:
            cl.user_follow(user)
            FOLLOWED_USERS[account_name].append(user)
            print(f"✅ Followed {user}")
            time.sleep(random.randint(30, 120))  # Random delay
        except Exception as e:
            print(f"❌ Error following {user}: {e}")

    # Save followed users
    save_followed_users()

    # Unfollow oldest follows after a certain threshold
    if len(FOLLOWED_USERS[account_name]) > 200:
        to_unfollow = FOLLOWED_USERS[account_name][:50]
        for user in to_unfollow:
            try:
                cl.user_unfollow(user)
                FOLLOWED_USERS[account_name].remove(user)
                print(f"🚀 Unfollowed {user}")
                time.sleep(random.randint(30, 120))  # Random delay
            except Exception as e:
                print(f"❌ Error unfollowing {user}: {e}")

        # Save updates
        save_followed_users()

# Function to schedule tasks with random variation
def schedule_random(account_name, base_hour):
    """Schedules job at a randomized time ±30 min from base_hour"""
    offset = random.randint(-30, 30)  # Random variation in minutes
    random_time = (datetime.strptime(base_hour, "%H:%M") + timedelta(minutes=offset)).strftime("%H:%M")
    schedule.every().day.at(random_time).do(lambda: follow_unfollow(account_name))
    print(f"⏰ Scheduled {account_name} at {random_time}")

# Schedule 4 tasks per day per account with variation
for base_time in ["06:00", "12:00", "18:00", "00:00"]:  # Adjust times as needed
    schedule_random("ig_1", base_time)
    schedule_random("ig_2", base_time)

# Keep script running
while True:
    schedule.run_pending()
    time.sleep(30)
