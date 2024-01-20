# Importing dependencies
import os
import json
import praw
import prawcore
import datetime
import csv
from prompt_toolkit.shortcuts import ProgressBar
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.shortcuts import button_dialog, prompt, yes_no_dialog, message_dialog, input_dialog, radiolist_dialog, checkboxlist_dialog, print_formatted_text
import tkinter as tk
from tkinter import filedialog
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

analyzer = SentimentIntensityAnalyzer()

# TODO:
"""
- fix the column_order list requirement in add_dicts_to_csv()
- fix select_or_create_csv() because when selecting a file you can cancel the filedialog and it will crash the program [DONE]
- implement exception handling
- limit subreddit_search_number in main() to only handle integers [DONE]
- flush the loading screen in RedditScrapeFunctions.autoScraper() [DONE]
- add more information to loading screen in RedditScrapeFunctions.autoScraper() so people know what is being loaded [DONE]
- [URGENT] Create a toggle for 'New', 'Hot', etc.
- [URGENT] Use last saved credentials
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
    bot.autoScraper("python", search_limit=10)
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
        sentimentAnalyzer = SentimentIntensityAnalyzer()

        while True:
            login_style = radiolist_dialog(
                title="Login Option",
                text="How would you like to log in?",
                values=[
                    (True, "Saved Credentials"),
                    (False, "Manual Login")
                ]
            ).run()

            profile_login_cancelled = False

            if login_style:
                if os.path.exists(os.getenv('APPDATA') + '\\redditscraper\\login_details.json'):
                    pass
                else:
                    if not os.path.exists(os.getenv('APPDATA') + '\\redditscraper'):
                        os.makedirs(os.getenv('APPDATA') + '\\redditscraper')
                    with open(os.getenv('APPDATA') + '\\redditscraper\\login_details.json', 'w') as file:
                        empty_json = {}
                        json.dump(empty_json, file)
                
                with open(os.getenv('APPDATA') + '\\redditscraper\\login_details.json', 'r') as file:
                    extracted_user_data = json.load(file)
                    json_extracted_usernames = list(extracted_user_data.keys())
                
                login_username_list = []

                for i in range(len(json_extracted_usernames)):
                    login_username_list.append((json_extracted_usernames[i], json_extracted_usernames[i]))

                login_username_list.append(('new', 'Add a new profile'))

                chosen_login_profile = radiolist_dialog(
                title="Login",
                text="Select your login profile",
                values=login_username_list
                ).run()

                if chosen_login_profile is None:
                    profile_login_cancelled = True
                elif chosen_login_profile == 'new':
                    new_profile_creation_cancelled = False
                    while new_profile_creation_cancelled == False:
                        new_database_username_entry = input_dialog(
                            title='New Details',
                            text='Please enter the client ID of the API account:').run()
                        new_database_password_entry = input_dialog(
                            title='New Details',
                            text='Please enter the secret of the API account:').run()
                        new_database_name_entry = input_dialog(
                            title='New Details',
                            text='Please enter the name by which you\'d like to remember the entry').run()
                        if new_database_username_entry == "" or new_database_password_entry == "":
                            new_profile_creation_cancelled_dialog_confirmation = yes_no_dialog(
                                title='Warning',
                                text='You did not enter a client ID or secret. Do you want retry?').run()
                            if new_profile_creation_cancelled_dialog_confirmation:
                                pass
                            else:
                                new_profile_creation_cancelled = True
                        else:
                            new_profile = {
                                'client_id': new_database_username_entry,
                                'client_secret': new_database_password_entry
                                }
                            extracted_user_data[new_database_name_entry] = new_profile
                            with open(os.getenv('APPDATA') + '\\redditscraper\\login_details.json', 'w') as file:
                                json.dump(extracted_user_data, file, indent=4)
                            profile_login_cancelled = True
                            break
                else:
                    reddit_client_id = extracted_user_data[chosen_login_profile]['client_id']
                    reddit_client_secret = extracted_user_data[chosen_login_profile]['client_secret']
                    reddit_user_agent = input_dialog(
                        title='Input Required',
                        text='Please enter a user agent name.\n(e.g. "MyRedditBot vX.X by /u/YourRedditName"):').run()
            else:
                reddit_client_id = input_dialog(
                    title='Credentials Required',
                    text='Please enter your Reddit API client ID:').run()

                reddit_client_secret = input_dialog(
                    title='Credentials Required',
                    text='Please enter your Reddit API client secret:').run()

                reddit_user_agent = input_dialog(
                    title='Credentials Required',
                    text='Please enter a user agent name.\n(e.g. "MyRedditBot vX.X by /u/YourRedditName"):').run()

            if not profile_login_cancelled:
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
                        text='Your ID or secret is incorrect.\n\nPlease enter it again!').run()
            else:
                profile_login_cancelled = False
                pass

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

    def autoScraper(self, subreddit, search_limit=1):
        """
        Scrapes information from a specified subreddit using the Reddit API.

        Args:
            subreddit (str): The name of the subreddit to scrape.
            search_limit (int, optional): The maximum number of posts to scrape. Defaults to 1.

        Returns:
            dict: A dictionary where each key is the post ID and the corresponding value is a dictionary containing the scraped information for each post.
        """
        dict_template = {
            "source": "",
            "post_title": "",
            "post_id": "",
            "date": "",
            "author": "",
            "upvotes": "",
            "post_url": "",
            "comment_count": "",
            "post_body": "",
            "sentiment": ""
        }

        return_dict = {}

        html_title = HTML('Downloading ' + str(search_limit) + ' Reddit entries...')
        html_label = HTML('<ansired>Download progress</ansired>: ')

        with ProgressBar(title=html_title) as pb:
            for submission in pb(self.reddit.subreddit(subreddit).hot(limit=search_limit), total=search_limit, label=html_label):
                new_dict = dict_template.copy()

                new_dict["source"] = "reddit"
                new_dict["post_title"] = str(submission.title).encode('utf-8', errors='ignore').decode('utf-8')
                new_dict["post_id"] = str(submission.id)
                new_dict["date"] = str(datetime.datetime.fromtimestamp(submission.created).date())
                new_dict["author"] = str(submission.author).encode('utf-8', errors='ignore').decode('utf-8')
                new_dict["upvotes"] = str(submission.score)
                new_dict["post_url"] = str(submission.url).encode('utf-8', errors='ignore').decode('utf-8')
                new_dict["comment_count"] = str(len(submission.comments))
                new_dict["post_body"] = str(submission.selftext).encode('utf-8', errors='ignore').decode('utf-8')
                new_dict["sentiment"] = analyzer.polarity_scores(str(submission.selftext).encode('utf-8', errors='ignore').decode('utf-8'))['compound']
                return_dict[hash(str(submission.id))] = new_dict

        os.system('cls')
        return return_dict
    
    def manualScraper(self, subreddit, search_limit=1):
        """
        Scrapes information from a specified subreddit using the Reddit API.

        Args:
            subreddit (str): The name of the subreddit to scrape.
            search_limit (int, optional): The maximum number of posts to scrape. Defaults to 1.

        Returns:
            dict: A dictionary where each key is the post ID and the corresponding value is a dictionary containing the scraped information for each post.
        """
        dict_template = {
            "source": "",
            "post_title": "",
            "post_id": "",
            "date": "",
            "author": "",
            "upvotes": "",
            "post_url": "",
            "comment_count": "",
            "post_body": "",
            "subject": "",
            "problem": "",
            "sentiment": ""
        }

        return_dict = {}

        html_title = HTML('Downloading ' + str(search_limit) + ' Reddit entries...')
        html_label = HTML('<ansired>Download progress</ansired>: ')

        os.system('cls')

        with ProgressBar(title=html_title) as pb:
            subreddit_posts = pb(self.reddit.subreddit(subreddit).hot(limit=search_limit), total=search_limit, label=html_label)

        os.system('cls')

        for submission in subreddit_posts:
            new_dict = dict_template.copy()

            new_dict["source"] = "reddit"
            new_dict["post_title"] = str(submission.title).encode('utf-8', errors='ignore').decode('utf-8')
            new_dict["post_id"] = str(submission.id)
            new_dict["date"] = str(datetime.datetime.fromtimestamp(submission.created).date())
            new_dict["author"] = str(submission.author).encode('utf-8', errors='ignore').decode('utf-8')
            new_dict["upvotes"] = str(submission.score)
            new_dict["post_url"] = str(submission.url).encode('utf-8', errors='ignore').decode('utf-8')
            new_dict["comment_count"] = str(len(submission.comments))
            new_dict["post_body"] = str(submission.selftext).encode('utf-8', errors='ignore').decode('utf-8')
            new_dict["sentiment"] = analyzer.polarity_scores(str(submission.selftext).encode('utf-8', errors='ignore').decode('utf-8'))['compound']

            print_formatted_text(HTML('<style bg="yellow" fg="black">You can find the post here below: </style>\n'))

            print('Title: ' + str(submission.title))

            print('\n' + str(submission.selftext))

            # MAKE PRETTY
            prompt(HTML('\n<style bg="yellow" fg="black">Press ENTER to continue.</style>\n'))

            os.system('cls')

            while True:
                subject_box_choice = checkboxlist_dialog(
                    title="Options",
                    text="What subjects were discussed in this topic?",
                    values=[
                        ("math", "Math"),
                        ("science", "Sciences"),
                        ("lang", "Language"),
                        ("societies", "Individuals and Societies"),
                        ("arts", "Arts"),
                        ("misc", "Misc"),
                        ("skip", "Skip this post")
                    ]
                ).run()

                if subject_box_choice is None:
                    cancel_options = yes_no_dialog(
                        title='Warning',
                        text='You just pressed cancel. You\'ll stop the scrape and begin the save process. Do you still wish to cancel?').run()
                    if cancel_options:
                        return return_dict
                elif subject_box_choice == ['skip']:
                    break
                else:
                    new_dict["subject"] = subject_box_choice
                    break

            if subject_box_choice == ['skip']:
                pass
            else:
                while True:
                    problem_box_choice = checkboxlist_dialog(
                        title="Options",
                        text="What problems were discussed in this topic?",
                        values=[
                            ("teachers", "Lack of quality teachers/teaching"),
                            ("ia", "Need college support"),
                            ("workload", "Too high workload"),
                            ("confusing", "IB is too confusing"),
                            ("resources", "Bad/not enough resources"),
                            ("college", "Need college guidance"),
                            ("management", "Difficulties with time management or organization"),
                            ("mental", "Mental health issues"),
                            ("structure", "Need college guidance"),
                            ("langbarrier", "Language barrier"),
                        ]
                    ).run()

                    if problem_box_choice is None:
                        cancel_options = yes_no_dialog(
                            title='Warning',
                            text='You just pressed cancel. You\'ll stop the scrape and begin the save process. Do you still wish to cancel?').run()
                        if cancel_options:
                            return_dict[hash(str(submission.id))] = new_dict
                            return return_dict
                    else:
                        new_dict["problem"] = problem_box_choice
                        break
            
            if subject_box_choice != "skip":
                return_dict[hash(str(submission.id))] = new_dict

            os.system('cls')

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
            columns = ['source', 'date', 'post_title', 'post_id', 'author', 
                    'upvotes', 'post_url', 'comment_count', 'post_body', 'sentiment', 'subject', 'problem']

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
                   'upvotes', 'post_url', 'comment_count', 'post_body', 'sentiment', 'subject', 'problem']

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
                ("option3", "Exit"),
            ]
        ).run()
    
    return main_menu_result

def main():

    bot = RedditScrapeFunctions()

    # Main menu
    while True:
        main_menu_result = main_menu()

        if main_menu_result == 'option3':
            exit()
        elif main_menu_result == 'option1':
            scraping_menu_result = radiolist_dialog(
                title="Menu",
                text="Choose an option.",
                values=[
                    ("manual", "Manual Scraping"),
                    ("auto", "Automatic Scraping"),
                    ("mainmenu", "Return to Main Menu"),
                ]
            ).run()
            if scraping_menu_result == "auto":
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
                user_chosen_csv_dir = select_or_create_csv()
                scrape_results = bot.autoScraper(subreddit=user_menu_subreddit_choice, search_limit=subreddit_search_number)
                unnested_scrape_results = extract_first_level_nested_dicts(scrape_results)
                add_dicts_to_csv(dicts=unnested_scrape_results, csv_filename=user_chosen_csv_dir)
                message_dialog(
                            title='Process Completed',
                            text='You can find your updated CSV in ' + str(user_chosen_csv_dir)).run()
            elif scraping_menu_result == "manual":
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
                user_chosen_csv_dir = select_or_create_csv()
                scrape_results = bot.manualScraper(subreddit=user_menu_subreddit_choice, search_limit=subreddit_search_number)
                unnested_scrape_results = extract_first_level_nested_dicts(scrape_results)
                add_dicts_to_csv(dicts=unnested_scrape_results, csv_filename=user_chosen_csv_dir)
                message_dialog(
                            title='Process Completed',
                            text='You can find your updated CSV in ' + str(user_chosen_csv_dir)).run()
            elif scraping_menu_result == "mainmenu":
                pass

main()