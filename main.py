"""  
 This file is part of *reddit-spammer*.
 Copyright (C) *2024* *ilovethensa*

 *reddit-spammer* is free software: you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation, either version 3 of the License, or
 (at your option) any later version.

 This program is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.

 You should have received a copy of the GNU General Public License
 along with this program.  If not, see <http://www.gnu.org/licenses/>.
 """
import random
import string
import re
import time
import json
import sys
import os
import schedule
from playwright.sync_api import Playwright, sync_playwright
from pynator import EmailNator
from random_username.generate import generate_username
from playwright_stealth import stealth_sync
from playwright_recaptcha import recaptchav2
# Initialize the EmailNator client
client = EmailNator()


def save_info_to_file(username, email, password, filename):
    # Create account dictionary
    account = {
        "username": username,
        "email": email,
        "password": password
    }

    try:
        # Try to read existing JSON data
        with open(filename, 'r') as file:
            accounts = json.load(file)
    except FileNotFoundError:
        # If file does not exist, create an empty list
        accounts = []

    # Append new account to the list
    accounts.append(account)

    # Write updated list of accounts to JSON file
    with open(filename, 'w') as file:
        json.dump(accounts, file, indent=4)

def generate_password(length=20):
    """Generate a random password."""
    characters = string.ascii_letters + string.digits
    password = ''.join(random.choice(characters) for _ in range(length))
    print("generated password!")
    return password

def find_reddit_url(html_content):
    """Find the Reddit verification URL in HTML content."""
    pattern = re.compile(
        r'https://www\.reddit\.com/user/[^/]+/\?correlation_id=[^&]+&amp;email_type=verify_email&amp;ref=verify_email&amp;ref_campaign=verify_email&amp;ref_source=email'
    )
    match = pattern.search(html_content)
    if match:
        return match.group(0)
    else:
        return None
def get_random_proxy(filename):
    with open(filename, 'r') as file:
        proxies = file.readlines()
    return random.choice(proxies).strip()

def run(playwright: Playwright, email, password, username) -> None:
    """Automate the sign-up process on Reddit."""
    print("opening chromium...")
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    stealth_sync(page)
    print("going to reddit.com...")
    page.goto("https://old.reddit.com/")
    page.wait_for_load_state('load')
    print("inputting email...")
    page.get_by_role("link", name="sign up").click()
    page.get_by_role("textbox").fill(email)
    page.wait_for_load_state('load')
    print("pressing continue...")
    page.get_by_role("button", name="Continue").click()
    print("filling in password and username...")
    page.locator("input[name=\"password\"]").fill(password)
    page.locator("input[name=\"username\"]").fill(username)
    page.wait_for_load_state('load')
    print("checking if captcha exists...")
    # Check if captcha exists
    try:
        page.wait_for_selector("body > shreddit-app > shreddit-overlay-display > div.recaptcha > div > div > iframe", timeout=10000)  # Timeout in milliseconds
        print("solving captcha...")
        with recaptchav2.SyncSolver(page) as solver:
            token = solver.solve_recaptcha(wait=True)
            print(token)
    except Exception as e:
        print(f"no captcha")
    print("clicking continue...")
    time.sleep(3)
    page.wait_for_selector("#register > faceplate-tabpanel > auth-flow-modal:nth-child(2) > div.w-100")
    page.get_by_role("button", name="Continue").click()
    page.wait_for_load_state('load')
    page.wait_for_selector("span > shreddit-async-loader > faceplate-tracker > ob-gender-selection > auth-flow-modal > faceplate-tracker > button > span > span > span")
    print("clicking skip...")
    page.get_by_role("button", name="Skip").click()
    page.wait_for_load_state('load')
    print("selecting interests...")
    page.get_by_role("checkbox", name="Bulgaria").click()
    page.wait_for_load_state('load')
    print("clicking continue...")
    page.get_by_role("button", name="Continue").click()
    print("closing browser...")
    context.close()
    browser.close()

def login(username, password, playwright):
    print("opening chromium...")
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    page.goto("https://www.reddit.com/login", timeout=100000)
    page.wait_for_load_state('load')
    page.locator("input[name=\"username\"]").fill(username)
    page.locator("input[name=\"password\"]").click()
    page.locator("input[name=\"password\"]").fill(password)
    page.get_by_role("button", name="Log In").click()
    time.sleep(5)
    page.goto("https://reddit.com", timeout=100000)
    page.wait_for_load_state('load')
    print("logged in...")
    return page, context, browser

def post(title, input_file, page):
    print("trying to post...")
    page.reload()
    subreddit = random.choice(open('subreddits.txt').readlines()).strip()
    page.goto(f"https://www.reddit.com/r/{subreddit}/submit/?type=IMAGE", timeout=100000)
    page.get_by_role("textbox", name="Title *").fill(title)
    page.get_by_role("button", name="Add flair and tags").click()
    page.get_by_role("radio", name="HUMOUR").click()
    page.get_by_role("button", name="Add", exact=True).click()
    with page.expect_file_chooser() as fc_info:
        page.get_by_role("button", name="Upload files").click()
    file_chooser = fc_info.value
    file_chooser.set_files(input_file)
    time.sleep(10)
    page.locator("#submit-post-button").click()

def get_propaganda():
    folder_path = 'propaganda'
    try:
        files = os.listdir(folder_path)
        if files:
            return os.path.join(folder_path, random.choice(files))
        else:
            return None
    except FileNotFoundError:
        return None

def load_accounts(file_path='accounts.json'):
    with open(file_path, 'r') as file:
        accounts = json.load(file)
    return accounts


def upload(account, playwright):
    page, context, browser = login(account['username'], account['password'], playwright)
    post(random.choice(open('titles.txt').readlines()).strip(), get_propaganda(), page)

def new(playwright):
    # Generate random username, email, and password
        username = generate_username(1)[0] + ' '.join(map(str, [random.randint(1, 100) for _ in range(3)])).replace(" ", "")
        password = generate_password()
        email = client.generate_email()

        print("username: ", username)
        print("email: ", email)
        print("password: ", password)

        # Run the automation script
        run(playwright, email, password, username)
        print("saving account to json...")
        save_info_to_file(username, email, password, "accounts.json")
        print("waiting for email...")
        time.sleep(20)  # Wait for emails to arrive

        # Check for verification email and print the verification URL
        messages = client.get_messages(email)
        for message in messages:
            print("dupe \n")
            print(message)
            if "Verify your Reddit email address" in message.subject:
                url = find_reddit_url(client.get_message(email, message.message_id))
                print(url)
                print("verifying account...")
                browser = playwright.chromium.launch(headless=False)
                context = browser.new_context()
                page = context.new_page()
                stealth_sync(page)
                page.goto(url)
                page.wait_for_load_state('load')
                print("account verified...")
                print("closing browser...")
                context.close()
                browser.close()

def run_upload_every_hour(playwright):
    accounts = load_accounts()
    account = random.choice(accounts)
    upload(account, playwright)


def main():
    """Main entry point of the script."""
    with sync_playwright() as playwright:
        if len(sys.argv) > 1:
            if sys.argv[1] == "new":
                new(playwright)
            elif sys.argv[1] == "upload":
                accounts = load_accounts()
                account = random.choice(accounts)
                print(account)
                upload(account, playwright)
            elif sys.argv[1] == "nonstop":
                # Schedule the upload function to run every hour
                schedule.every().hour.do(run_upload_every_hour, playwright)
                while True:
                    schedule.run_pending()
                    time.sleep(1)
            else:
                print("Invalid subcommand. Use 'new', 'upload', or 'nonstop'.")
        else:
            print("No subcommand provided. Use 'new', 'upload', or 'nonstop'.")

                

if __name__ == "__main__":
    main()
