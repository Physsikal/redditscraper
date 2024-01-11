# Importing dependencies
import sys
import praw
import prawcore
import datetime
import csv
from prompt_toolkit.shortcuts import ProgressBar
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.shortcuts import yes_no_dialog
from prompt_toolkit.shortcuts import message_dialog
from prompt_toolkit.shortcuts import input_dialog
from prompt_toolkit.shortcuts import radiolist_dialog
import tkinter as tk
from tkinter import filedialog

# TODO:
"""
- fix the column_order list requirement in add_dicts_to_csv()
- fix select_or_create_csv() because when selecting a file you can cancel the filedialog and it will crash the program [DONE]
- implement exception handling
- limit subreddit_search_number in main() to only handle integers [DONE]
- flush the loading screen in RedditScrapeFunctions.scraper() [DONE]
- add more information to loading screen in RedditScrapeFunctions.scraper() so people know what is being loaded [DONE]
- [URGENT] Create a toggle for 'New', 'Hot', etc.
"""

# CHANGELOG:
"""
v1.1:
* Added error handling for non-existant subreddits
* Added filedialog cancel protection
* Added information to the loading bar so users know what is being downloaded
"""

class RedditScrapeFunctions:
    """
    The RedditScrapeFunctions class is responsible for initializing the Reddit API client and providing methods to scrape information from a specified subreddit using the Reddit API.

    Example Usage:
    ```python
    bot = RedditScrapeFunctions()

    # Initialize the Reddit API client by providing the client ID, client secret, and user agent name
    bot.__init__()

    # Check if a subreddit exists
    bot.test_if_subreddit_exists("python")

    # Scrape information from a subreddit
    bot.scraper("python", search_limit=10)
    ```
    """

    def __init__(self):
        """
        Initializes the Reddit API client by taking user input for the client ID, client secret, and user agent name.
        It also checks the authentication by attempting to fetch a subreddit attribute.

        Args:
            None

        Returns:
            None
        """
        while True:
            reddit_client_id = input_dialog(
                title='Credentials Required',
                text='Please enter your Reddit API client ID:').run()

            reddit_client_secret = input_dialog(
                title='Credentials Required',
                text='Please enter your Reddit API client secret:').run()

            reddit_user_agent = input_dialog(
                title='Credentials Required',
                text='Please enter a user agent name.\n(e.g. "MyRedditBot vX.X by /u/YourRedditName"):').run()

            # PRAW instantiation
            self.reddit = praw.Reddit(
                # Your Reddit app ID
                client_id=reddit_client_id,
                # Your Reddit app secret
                client_secret=reddit_client_secret,
                # App identifier (ex. 'RedditBot 1.0 by /u/RedditName')
                user_agent=reddit_user_agent,
            )

            # The only way to check authentication w/o using the user pass and username is by
            # trying to fetch a subreddit atribute.
            try:
                subreddit = self.reddit.subreddit("python")
                for post in subreddit.hot(limit=1):
                    post.title
                break
            except Exception as e:
                message_dialog(
                    title='Warning',
                    text='Your ID or secret were incorrect.\nPlease enter them again.').run()

    def test_if_subreddit_exists(self, subreddit_name):
        """
        Checks if a subreddit exists by attempting to fetch a subreddit attribute.

        Args:
            subreddit_name (str): The name of the subreddit to check.

        Returns:
            bool: True if the subreddit exists, False otherwise.
        """
        try:
            for post in self.reddit.subreddit(subreddit_name).hot(limit=1):
                post.title
                return True
        except prawcore.exceptions.NotFound:
            message_dialog(
                        title='Warning',
                        text='This subreddit does not exist!').run()
            return False
        except Exception as e:
            message_dialog(
                        title='Warning',
                        text='An error occured or this subreddit does not exist!').run()
            return False

    def scraper(self, subreddit, search_limit=1):
        """
        Scrapes information from a specified subreddit using the Reddit API.

        Args:
            subreddit (str): The name of the subreddit to scrape.
            search_limit (int, optional): The maximum number of posts to scrape. Defaults to 1.

        Returns:
            dict: A dictionary where each key is the post ID and the corresponding value is a dictionary containing the scraped information for each post.
        """
        dict_template = {
            "platform": "",
            "post_title": "",
            "post_id": "",
            "date": "",
            "author": "",
            "upvotes": "",
            "post_url": "",
            "comment_count": "",
            "post_body": ""
        }

        return_dict = {}

        html_title = HTML('Downloading ' + str(search_limit) + ' Reddit entries...')
        html_label = HTML('<ansired>Download progress</ansired>: ')

        with ProgressBar(title=html_title) as pb:
            for submission in pb(self.reddit.subreddit(subreddit).hot(limit=search_limit), total=search_limit, label=html_label):
                new_dict = dict_template.copy()

                new_dict["platform"] = "reddit"
                new_dict["post_title"] = str(submission.title).encode('utf-8', errors='ignore').decode('utf-8')
                new_dict["post_id"] = str(submission.id)
                new_dict["date"] = str(datetime.datetime.fromtimestamp(submission.created).date())
                new_dict["author"] = str(submission.author).encode('utf-8', errors='ignore').decode('utf-8')
                new_dict["upvotes"] = str(submission.score)
                new_dict["post_url"] = str(submission.url).encode('utf-8', errors='ignore').decode('utf-8')
                new_dict["comment_count"] = str(len(submission.comments))
                new_dict["post_body"] = str(submission.selftext).encode('utf-8', errors='ignore').decode('utf-8')
                return_dict[hash(str(submission.id))] = new_dict

        sys.stdout.flush()
        return return_dict

def select_or_create_csv():
    # Initialize Tkinter
    root = tk.Tk()
    root.withdraw()  # Hide the main window

    while True:
        # Ask the user to select an option
        result = yes_no_dialog(
            title='File Option',
            text='Do you already have a CSV?').run()

        if result == True:
            # File selection dialog for when user selected yes
            file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
            # File path gets returned
            if file_path:
                return file_path
            # If the user cancelled it will not return the file path and continue the loop
        elif result == False:
            # Informs the user that the file will be created
            message_dialog(
                title='Information',
                text='A file will now be created for you.').run()
            
            # Define default columns
            columns = ['platform', 'date', 'post_title', 'post_id', 'author', 
                    'upvotes', 'post_url', 'comment_count', 'post_body', 'sentiment']

            # Saving file dialog
            file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
            # If it's detected that a file has been selected it will continue else it will go back to the yes no dialog
            if file_path:
                # Create a new CSV file with specified columns
                with open(file_path, 'w', newline='', encoding='utf-8') as file:
                    writer = csv.DictWriter(file, fieldnames=columns)
                    writer.writeheader()
                return file_path

def extract_first_level_nested_dicts(main_dict):
    """
    Extracts the first level nested dictionaries from a given main dictionary.

    Args:
    - main_dict (dict): The main dictionary from which the first level nested dictionaries need to be extracted.

    Returns:
    - nested_dicts (list): A list containing the first level nested dictionaries from the main_dict.
    """

    nested_dicts = []

    for key, value in main_dict.items():
        if isinstance(value, dict):
            nested_dicts.append(value)  # Add only the first level nested dictionary

    return nested_dicts

def add_dicts_to_csv(dicts, csv_filename=None):
    """
    Appends the values from a list of dictionaries to a CSV file.

    Args:
        dicts (list of dictionaries): A list of dictionaries containing the data to be added to the CSV file.
        csv_filename (string, optional): The filename of the CSV file to which the data will be appended. Defaults to None.

    Returns:
        None: The function does not return any value. It appends the values from the dictionaries to the CSV file.
    """

    if csv_filename == None:
        return
    
    with open(csv_filename, 'a', encoding='utf-8', newline='') as csvfile:
        writer = csv.writer(csvfile)

        column_order = ['platform', 'date', 'post_title', 'post_id', 'author', 
                   'upvotes', 'post_url', 'comment_count', 'post_body', 'sentiment']

        # For each dictionary, add its values to the CSV file
        for d in dicts:
            row = [d.get(key, '') for key in column_order]  # Get values based on the column order, default to empty string
            writer.writerow(row)

def main_menu():
    main_menu_result = radiolist_dialog(
            title="Menu",
            text="Choose an option.",
            values=[
                ("option1", "Scrape a Subreddit"),
                ("option2", "Exit"),
            ]
        ).run()
    
    return main_menu_result

def main():

    bot = RedditScrapeFunctions()

    # Main menu
    while True:
        main_menu_result = main_menu()

        if main_menu_result == 'option2':
            exit()
        elif main_menu_result == 'option1':
            while True:
                user_menu_subreddit_choice = input_dialog(
                        title='Information Required',
                        text='Please enter the Subreddit name you\'d like to scrape:').run()
                # This if statement takes a Subreddit and if it exists let's it through
                if bot.test_if_subreddit_exists(user_menu_subreddit_choice):
                    break
            # FROM THIS POINT FORWARD CODE NEEDS TO BE OPTIMIZED
            while True:
                subreddit_search_number = input_dialog(
                    title='Information Required',
                    text='How many entries would you like to collect (e.g. 1-1000)?:').run()
                if subreddit_search_number.isdigit():
                    if int(subreddit_search_number) > 0 and int(subreddit_search_number) < 1001:
                        break
            subreddit_search_number = int(subreddit_search_number)
            scrape_results = bot.scraper(subreddit=user_menu_subreddit_choice, search_limit=subreddit_search_number)
            unnested_scrape_results = extract_first_level_nested_dicts(scrape_results)
            user_chosen_csv_dir = select_or_create_csv()
            add_dicts_to_csv(dicts=unnested_scrape_results, csv_filename=user_chosen_csv_dir)
            message_dialog(
                        title='Process Completed',
                        text='You can find your updated CSV in ' + str(user_chosen_csv_dir)).run()

main()