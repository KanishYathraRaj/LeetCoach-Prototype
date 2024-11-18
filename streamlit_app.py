from leetcode_scraper import LeetcodeScraper
import streamlit as st
import os
from langchain_groq import ChatGroq
import requests
import json , pandas as pd

user_contest_rating= 0

def get_profile_data(username):
    scraper = LeetcodeScraper()
    profile_data = scraper.scrape_user_profile(username)
    return profile_data

def format_userdata(profile_data):
    st.write("Profile Data:",profile_data)
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

    st.sidebar.title("Performance Overview")
    st.sidebar.markdown(f"**Username**: {username}")
    st.sidebar.markdown(f"**Total Problems Solved**: {total_solved_problems}")
    st.sidebar.markdown(f"**Easy Problems Solved**: {total_solved_problems_easy}")
    st.sidebar.markdown(f"**Medium Problems Solved**: {total_solved_problems_medium}")
    st.sidebar.markdown(f"**Hard Problems Solved**: {total_solved_problems_hard}")
    st.sidebar.markdown(f"**Active Years**: {', '.join(map(str, activeYears))}")
    st.sidebar.markdown(f"**Longest Streak**: {streak} days")
    st.sidebar.markdown(f"**Total Active Days**: {totalActiveDays} days")
    st.sidebar.markdown(f"**Contests Attended**: {attendedContestsCount}")
    st.sidebar.markdown(f"**Contest Rating**: {rating}")
    st.sidebar.markdown(f"**Global Ranking (Contests)**: {global_ranking}")
    st.sidebar.markdown(f"**Global Ranking (Problem Count)**: {rank_in_problem_count}")

    return userdata

def get_problem_rating():
    url = "https://zerotrac.github.io/leetcode_problem_rating/data.json"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        return data
    else:
        st.error(f"Failed to retrieve data: {response.status_code}")
        return []

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

        # Existing filter controls
        min_rating, max_rating = st.slider(
            "Select Rating Range",
            min_value=int(df_filtered['Rating'].min()),
            max_value=int(df_filtered['Rating'].max()),
            value=(int(df_filtered['Rating'].min()), int(df_filtered['Rating'].max()))
        )
        min_id, max_id = st.slider(
            "Select Question ID Range",
            min_value=int(df_filtered['ID'].min()),
            max_value=int(df_filtered['ID'].max()),
            value=(int(df_filtered['ID'].min()), int(df_filtered['ID'].max()))
        )

        # Apply filters
        df_filtered = df_filtered[(df_filtered['Rating'] >= min_rating) & (df_filtered['Rating'] <= max_rating)]
        df_filtered = df_filtered[(df_filtered['ID'] >= min_id) & (df_filtered['ID'] <= max_id)]

        st.table(df_filtered[['ID', 'Title', 'Rating', 'Difficulty']])


def main():
    st.title("LeetCoach")

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        st.error("GROQ_API_KEY environment variable is not set. Please set it to use this app.")
        return

    # Initialize LLM
    llm = ChatGroq(
        model="llama-3.1-70b-versatile",
        temperature=1,
        max_tokens=None,
        timeout=None,
        max_retries=2,
        groq_api_key=api_key
    )

    username = st.text_input("Enter LeetCode Username:")

    if st.button("Analyze Me"):
        if username:
            try:
                profile_data = get_profile_data(username)
                userdata = format_userdata(profile_data)
                messages = [
                    (
                        "system",
                        "You are an expert programmer who can help me understand the performance of LeetCode users. You can use the following information to help me understand the performance of the user. dont generate any code.",
                    ),
                    ("human", userdata),
                ]
                ai_msg = llm.invoke(messages)
                st.write(ai_msg.content)


            except Exception as e:
                st.error(f"Error fetching or processing profile data: {e}")
        else:
            st.warning("Please enter a valid LeetCode username.")

    display_problems()

if __name__ == "__main__":
    if 'user_contest_rating' not in st.session_state:
        st.session_state.user_contest_rating = 0
    main()
