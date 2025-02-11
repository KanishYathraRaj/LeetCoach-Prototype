from leetcode_scraper import LeetcodeScraper
import streamlit as st
import os
from langchain_groq import ChatGroq
import requests
import pandas as pd
import base64
import json
import datetime
import firebase_admin
from firebase_admin import credentials, firestore

user_contest_rating = 0
data = []

def initialize_firebase():
    encoded_service_account_json = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")
    service_account_json = base64.b64decode(encoded_service_account_json).decode()
    service_account_info = json.loads(service_account_json)
    cred = credentials.Certificate(service_account_info)
    try:
        firebase_admin.initialize_app(cred)
    except ValueError:
        pass
    db = firestore.client()
    return db

def store_user_data(username, userdata):
    db = initialize_firebase()
    current_time = datetime.datetime.now()
    doc_ref = db.collection('leetcode_users_2').document(username)
    doc = doc_ref.get()
    if doc.exists:
        data = doc.to_dict()
        count = data.get('count', 0) + 1
    else:
        count = 1
    doc_ref.set({
        'username': username,
        'profile_data': userdata,
        'timestamp': current_time,
        'count': count,
    })
    st.toast(f"Successfully fetched the leetcode data of {username}...")

def get_profile_data(username):
    scraper = LeetcodeScraper()
    profile_data = scraper.scrape_user_profile(username)
    return profile_data

def format_userdata(profile_data):
    with st.sidebar.expander("Raw View Profile Data", expanded=False):
        st.write("Profile Data:", profile_data)
    username = "N/A"
    rank_in_problem_count = "N/A"
    aboutMe = "N/A"
    activeYears = "N/A"
    streak = "N/A"
    totalActiveDays = "N/A"
    total_solved_problems = "N/A"
    total_solved_problems_easy = "N/A"
    total_solved_problems_medium = "N/A"
    total_solved_problems_hard = "N/A"
    attendedContestsCount = "N/A"
    rating = "N/A"
    global_ranking = "N/A"

    # Check for userPublicProfile and nested matchedUser keys
    if 'userPublicProfile' in profile_data and profile_data['userPublicProfile'] is not None:
        matched_user = profile_data['userPublicProfile'].get('matchedUser', {})
        if matched_user:
            username = matched_user.get('username', 'N/A')
            profile = matched_user.get('profile', {})
            if profile:
                rank_in_problem_count = profile.get('ranking', 'N/A')
                aboutMe = profile.get('aboutMe', 'N/A')

    # Check for userProfileCalendar and nested matchedUser keys
    if 'userProfileCalendar' in profile_data and profile_data['userProfileCalendar'] is not None:
        matched_user_calendar = profile_data['userProfileCalendar'].get('matchedUser', {})
        if matched_user_calendar:
            user_calendar = matched_user_calendar.get('userCalendar', {})
            if user_calendar:
                activeYears = user_calendar.get('activeYears', 'N/A')
                streak = user_calendar.get('streak', 'N/A')
                totalActiveDays = user_calendar.get('totalActiveDays', 'N/A')

    # Check for userProblemsSolved and nested matchedUser keys
    if 'userProblemsSolved' in profile_data and profile_data['userProblemsSolved'] is not None:
        matched_user_solved = profile_data['userProblemsSolved'].get('matchedUser', {})
        if matched_user_solved:
            submit_stats = matched_user_solved.get('submitStatsGlobal', {}).get('acSubmissionNum', [])
            if submit_stats:
                total_solved_problems = submit_stats[0].get('count', 'N/A') if len(submit_stats) > 0 else 'N/A'
                total_solved_problems_easy = submit_stats[1].get('count', 'N/A') if len(submit_stats) > 1 else 'N/A'
                total_solved_problems_medium = submit_stats[2].get('count', 'N/A') if len(submit_stats) > 2 else 'N/A'
                total_solved_problems_hard = submit_stats[3].get('count', 'N/A') if len(submit_stats) > 3 else 'N/A'

    # Check for userContestRankingInfo and nested userContestRanking keys
    if 'userContestRankingInfo' in profile_data and profile_data['userContestRankingInfo'] is not None:
        contest_ranking = profile_data['userContestRankingInfo'].get('userContestRanking', {})
        if contest_ranking:
            attendedContestsCount = contest_ranking.get('attendedContestsCount', 'N/A')
            rating = contest_ranking.get('rating', 'N/A')
            if rating != 'N/A' and rating is not None:
                st.session_state.user_contest_rating = round(rating)
            global_ranking = contest_ranking.get('globalRanking', 'N/A')

    # Formatted user data for the LLM prompt
    userdata = f"""
    The username : {username} \n
    About me : {aboutMe} \n
    Total problem solved : {total_solved_problems} \n
    No of easy problems solved : {total_solved_problems_easy} \n
    No of medium problems solved : {total_solved_problems_medium} \n
    No of hard problems solved : {total_solved_problems_hard}
    Active years : {activeYears} \n
    Longest streak : {streak} days \n
    Total active days : {totalActiveDays} days \n
    No of contests attended : {attendedContestsCount} \n
    Contest rating : {rating} \n
    Global ranking in contest : {global_ranking} \n
    Global ranking in problem count : {rank_in_problem_count} \n
    """
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.info(f"**Username**: {username}")
        st.info(f"**Total Problems Solved**: {total_solved_problems}")
        st.info(f"**Easy Problems Solved**: {total_solved_problems_easy}")
        st.info(f"**Medium Problems Solved**: {total_solved_problems_medium}")
    with col2:
        st.info(f"**Hard Problems Solved**: {total_solved_problems_hard}")
        st.info(f"**Active Years**: {', '.join(map(str, activeYears))}")
        st.info(f"**Longest Streak**: {streak} days")
        st.info(f"**Total Active Days**: {totalActiveDays} days")
    with col3:
        st.info(f"**Contests Attended**: {attendedContestsCount}")
        st.info(f"**Contest Rating**: {rating}")
        st.info(f"**Global Ranking (Contests)**: {global_ranking}")
        st.info(f"**Global Ranking (Problem Count)**: {rank_in_problem_count}")

    return userdata

def get_problem_rating():
    if 'problem_data' not in st.session_state:
        url = "https://zerotrac.github.io/leetcode_problem_rating/data.json"
        response = requests.get(url)

        if response.status_code == 200:
            st.session_state.problem_data = response.json()
        else:
            st.error(f"Failed to retrieve data: {response.status_code}")
            st.session_state.problem_data = []
    return st.session_state.problem_data

def calculate_difficulty(rating, problem_rating):
    if rating - 100 <= problem_rating <= rating + 100:
        return "Medium"
    elif problem_rating < rating - 100:
        return "Easy"
    else:
        return "Hard"
    
def display_problems():
    st.title("LeetCode Problem Ratings Table")
    data = get_problem_rating()
    if data:
        df = pd.DataFrame(data)
        df['Rating'] = df['Rating'].astype(int)

        user_contest_rating = st.session_state.get('user_contest_rating', 0)
        df['Difficulty'] = df['Rating'].apply(lambda x: calculate_difficulty(user_contest_rating, x))

        columns_to_display = ['ID', 'Title', 'Rating', 'Difficulty']
        df_filtered = df[columns_to_display]

        st.sidebar.header("Filter Controls For Problem Ratings")
        # Existing filter controls
        min_rating, max_rating = st.sidebar.slider(
            "Select Rating Range",
            min_value=int(df_filtered['Rating'].min()),
            max_value=int(df_filtered['Rating'].max()),
            value=(int(df_filtered['Rating'].min()), int(df_filtered['Rating'].max()))
        )
        min_id, max_id = st.sidebar.slider(
            "Select Question ID Range",
            min_value=int(df_filtered['ID'].min()),
            max_value=int(df_filtered['ID'].max()),
            value=(int(df_filtered['ID'].min()), int(df_filtered['ID'].max()))
        )


        df_filtered = df_filtered[(df_filtered['Rating'] >= min_rating) & (df_filtered['Rating'] <= max_rating)]
        df_filtered = df_filtered[(df_filtered['ID'] >= min_id) & (df_filtered['ID'] <= max_id)]

        
        # Add pagination
        items_per_page = 10
        total_items = len(df_filtered)
        total_pages = (total_items // items_per_page) + (1 if total_items % items_per_page > 0 else 0)

        page_number = st.sidebar.number_input("Page Number", min_value=1, max_value=total_pages, value=1, step=1)
        start_idx = (page_number - 1) * items_per_page
        end_idx = start_idx + items_per_page

        df_paginated = df_filtered.iloc[start_idx:end_idx]
        st.table(df_paginated[['ID', 'Title', 'Rating', 'Difficulty']])

        st.write(f"Page {page_number} of {total_pages}")
        with st.expander("Logic Behind Problem Difficulty", expanded=False):
            st.info('''The Problem Rating based on your contest rating is calculated as follows:
            \n- If the problem rating is within ±100 of your contest rating, it is considered Medium.
            \n- If the problem rating is less than your contest rating - 100, it is considered Easy.
            \n- If the problem rating is greater than your contest rating + 100, it is considered Hard.''')
        
        st.expander("Show Entire Table", expanded=False).write(df_filtered)

def main():
    st.set_page_config(page_title="LeetCoach", page_icon=":rocket:", layout="wide")
    st.title("LeetCoach")
    st.markdown("""
        <style>
        .main {
            background-color: #f0f2f6;
            padding: 20px;
            border-radius: 10px;
        }
        .sidebar .sidebar-content {
            background-color: #f0f2f6;
            padding: 20px;
            border-radius: 10px;
        }
        .stButton>button {
            background-color: #4CAF50;
            color: white;
            border: none;
            padding: 10px 20px;
            text-align: center;
            text-decoration: none;
            display: inline-block;
            font-size: 16px;
            margin: 4px 2px;
            cursor: pointer;
            border-radius: 10px;
        }
        </style>
    """, unsafe_allow_html=True)

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        st.error("GROQ_API_KEY environment variable is not set. Please set it to use this app.")
        return

    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=1,
        max_tokens=None,
        timeout=None,
        max_retries=2,
        groq_api_key=api_key
    )

    with st.sidebar:
        st.title("LeetCoach")
        username = st.text_input("Enter LeetCode Username:")
        analyze_button = st.button("Analyze Me")

    if analyze_button:
        if username:
            try:
                profile_data = get_profile_data(username)
                userdata = format_userdata(profile_data)
                store_user_data(username, userdata)
                messages = [
                    (
                        "system",
                        "You are an expert programmer who can help me understand the performance of LeetCode users. You can use the following information to help me understand the performance of the user. dont generate any code.",
                    ),
                    ("human", userdata),
                ]
                ai_msg = llm.invoke(messages)
                st.header("Performance overview")
                st.success(ai_msg.content)
                st.snow()
                st.balloons()
                st.toast('Your Leetcode has been analyzed successfully!', icon='😍')
            except Exception as e:
                st.error(f"Error fetching or processing profile data: {e}")
        else:
            st.warning("Please enter a valid LeetCode username.")

    display_problems()
    st.sidebar.header("Just for fun")
    chat_input = st.sidebar.chat_input("Chat with me Serectly🫥!")
    if chat_input:
        messages = [(
                        "system",
                        "You are funny guy who talks to the user in a very funny and angry and roast them while answering their question. answer in 10 words.",
                    ),("human", chat_input)]
        ai_msg = llm.invoke(messages)
        st.toast(ai_msg.content, icon='😏') 

    st.success("Please give 'STAR' to the repo if you like the app :star:")

if __name__ == "__main__":
    if 'user_contest_rating' not in st.session_state:
        st.session_state.user_contest_rating = 0
    main()
