import streamlit as st
import matplotlib.pyplot as plt
from supabase import create_client, Client
import random
from datetime import datetime
import os

# Supabase Configuration
TRAVEL_API_LINK = "https://wbglxvwpytrehoipvzlr.supabase.co"
TRAVEL_API_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6IndiZ2x4dndweXRyZWhvaXB2emxyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Mzg1ODg4MDYsImV4cCI6MjA1NDE2NDgwNn0.eA-M-UNRlBrbMDpQQpnWZh9LxmfwlmD8WPX3k3IIhOQ"
travel_system = create_client(TRAVEL_API_LINK, TRAVEL_API_TOKEN)

# Generate random ID
def generate_id():
    return str(random.randint(100000, 999999))

# Base Travel Class and Subclasses
class TravelPlan:
    def __init__(self, traveler_name, trip_date):
        self.traveler_name = traveler_name
        self.trip_date = trip_date
        self.plan_code = f"TR{generate_id()}"
        self.traveler_info = []

class PlaneTravel(TravelPlan):
    def __init__(self, traveler_name, start_city, end_city, trip_date, traveler_count):
        super().__init__(traveler_name, trip_date)
        self.category = "Flight"
        self.start_city = start_city
        self.end_city = end_city
        self.traveler_count = traveler_count

    def show_info(self):
        info = f"{self.category} - ID: {self.plan_code}\nTraveler: {self.traveler_name}\nFrom: {self.start_city} to {self.end_city}\nDate: {self.trip_date}\nPassengers: {self.traveler_count}"
        if self.traveler_info:
            info += "\nPersons Details:\n" + "\n".join([f"- {t['name']}, Age: {t['age']}" for t in self.traveler_info])
        return info

class StayTravel(TravelPlan):
    def __init__(self, traveler_name, stay_name, trip_date, stay_duration):
        super().__init__(traveler_name, trip_date)
        self.category = "Hotel"
        self.stay_name = stay_name
        self.stay_duration = stay_duration

    def show_info(self):
        info = f"{self.category} - ID: {self.plan_code}\nTraveler: {self.traveler_name}\nHotel: {self.stay_name}\nDate: {self.trip_date}\nNights: {self.stay_duration}"
        if self.traveler_info:
            info += "\nPersons Details:\n" + "\n".join([f"- {t['name']}, Age: {t['age']}" for t in self.traveler_info])
        return info

class AdventureTravel(TravelPlan):
    def __init__(self, traveler_name, adventure_title, trip_date, group_size):
        super().__init__(traveler_name, trip_date)
        self.category = "Package"
        self.adventure_title = adventure_title
        self.group_size = group_size

    def show_info(self):
        info = f"{self.category} - ID: {self.plan_code}\nTraveler: {self.traveler_name}\nPackage: {self.adventure_title}\nDate: {self.trip_date}\nPersons: {self.group_size}"
        if self.traveler_info:
            info += "\nPersons Details:\n" + "\n".join([f"- {t['name']}, Age: {t['age']}" for t in self.traveler_info])
        return info

# Travel Stack
class TravelQueue:
    def __init__(self):
        self.queue = []

    def add(self, plan):
        self.queue.append(plan)

    def remove(self):
        if not self.is_empty():
            return self.queue.pop()
        raise Exception("No plans to remove")

    def is_empty(self):
        return len(self.queue) == 0

    def reset(self):
        self.queue = []

# Travel Organizer
class TravelOrganizer:
    def __init__(self, account_name):
        self.account_name = account_name
        self.plane_stats = {"Delhi-Mumbai": 5, "Mumbai-Goa": 3, "Bangalore-Chennai": 2, "Delhi-Kolkata": 1}
        self.stay_stats = {"Taj Palace": 4, "Oberoi": 3, "ITC Grand": 2, "Hyatt": 1}
        self.adventure_stats = {"Goa Getaway": 5, "Kerala Bliss": 2, "Rajasthan Royals": 3, "Himalayan Trek": 1}

    def store_plan(self, plan):
        try:
            record = {
                "booking_id": plan.plan_code,
                "username": self.account_name,
                "booking_type": plan.category,
                "details": plan.show_info(),
                "travel_date": plan.trip_date
            }
            result = travel_system.table("bookings").insert(record).execute()
            if result.data:
                self.update_stats(plan)
                return True
            return False
        except Exception as e:
            st.error(f"Error storing plan: {str(e)}")
            return False

    def retrieve_plans(self):
        try:
            result = travel_system.table("bookings").select("details").eq("username", self.account_name).execute()
            plans = result.data
            if plans:
                return "\n\n".join(plan["details"] for plan in plans)
            return "No plans found."
        except Exception as e:
            st.error(f"Error retrieving plans: {str(e)}")
            return "Error retrieving plans"

    def cancel_plan(self, plan_code, traveler_name=None):
        try:
            result = travel_system.table("bookings").select("*").eq("booking_id", plan_code).eq("username", self.account_name).execute()
            if result.data:
                plan_data = result.data[0]
                if traveler_name:
                    info_lines = plan_data["details"].split("\n")
                    info_section = False
                    new_info = []
                    traveler_removed = False
                    traveler_count = int(info_lines[4].split(": ")[1])
                    for line in info_lines:
                        if "Persons Details:" in line:
                            info_section = True
                            new_info.append(line)
                            continue
                        if info_section and line.startswith("- ") and traveler_name in line:
                            traveler_removed = True
                            traveler_count -= 1
                            continue
                        new_info.append(line)
                    if traveler_removed:
                        if plan_data["booking_type"] == "Flight":
                            new_info[4] = f"Passengers: {traveler_count}"
                        elif plan_data["booking_type"] == "Package":
                            new_info[4] = f"Persons: {traveler_count}"
                        travel_system.table("bookings").update({"details": "\n".join(new_info)}).eq("booking_id", plan_code).execute()
                        return True
                    st.error(f"Traveler {traveler_name} not found in plan {plan_code}.")
                    return False
                else:
                    travel_system.table("bookings").delete().eq("booking_id", plan_code).execute()
                    return True
            st.error(f"Plan code {plan_code} not found.")
            return False
        except Exception as e:
            st.error(f"Error canceling plan: {str(e)}")
            return False

    def find_plan(self, plan_code):
        try:
            result = travel_system.table("bookings").select("details").eq("username", self.account_name).eq("booking_id", plan_code).execute()
            if result.data:
                return result.data[0]["details"]
            return "Plan not found."
        except Exception as e:
            st.error(f"Error finding plan: {str(e)}")
            return "Error finding plan"

    def end_session(self):
        try:
            result = travel_system.table("bookings").select("details").eq("username", self.account_name).execute()
            plans = result.data
            if plans:
                travel_system.table("bookings").delete().eq("username", self.account_name).execute()
                return True
            return False
        except Exception as e:
            st.error(f"Error during session end: {str(e)}")
            return False

    def update_stats(self, plan):
        if plan.category == "Flight":
            route = f"{plan.start_city}-{plan.end_city}"
            self.plane_stats[route] = self.plane_stats.get(route, 0) + plan.traveler_count
        elif plan.category == "Hotel":
            self.stay_stats[plan.stay_name] = self.stay_stats.get(plan.stay_name, 0) + 1
        elif plan.category == "Package":
            self.adventure_stats[plan.adventure_title] = self.adventure_stats.get(plan.adventure_title, 0) + plan.group_size

    def show_trends(self):
        fig = plt.figure(figsize=(12, 8))
        
        plt.subplot(2, 2, 1)
        plt.bar(self.plane_stats.keys(), self.plane_stats.values(), color='skyblue')
        plt.title("Popular Flights")
        plt.ylabel("Count")
        plt.xticks(rotation=45)
        
        plt.subplot(2, 2, 2)
        plt.bar(self.stay_stats.keys(), self.stay_stats.values(), color='lightgreen')
        plt.title("Popular Hotels")
        plt.ylabel("Count")
        plt.xticks(rotation=45)
        
        plt.subplot(2, 2, 3)
        plt.bar(self.adventure_stats.keys(), self.adventure_stats.values(), color='salmon')
        plt.title("Popular Packages")
        plt.ylabel("Count")
        plt.xticks(rotation=45)

        total_planes = sum(self.plane_stats.values())
        total_stays = sum(self.stay_stats.values())
        total_adventures = sum(self.adventure_stats.values())
        total = total_planes + total_stays + total_adventures
        if total > 0:
            plane_pct = (total_planes / total) * 100
            stay_pct = (total_stays / total) * 100
            adventure_pct = (total_adventures / total) * 100
            explode = [0.1 if pct == max(plane_pct, stay_pct, adventure_pct) else 0 for pct in [plane_pct, stay_pct, adventure_pct]]
            plt.subplot(2, 2, 4)
            labels = ['Flights', 'Hotels', 'Packages']
            sizes = [total_planes, total_stays, total_adventures]
            plt.pie(sizes, explode=explode, labels=labels, autopct='%1.1f%%', startangle=90, colors=['skyblue', 'lightgreen', 'salmon'])
            plt.title("Trend Categories")
            plt.axis('equal')

        plt.tight_layout()
        return fig

# Route Planner
class RoutePlanner:
    def __init__(self):
        self.paths = {
            "Delhi": ["Mumbai", "Bangalore", "Kolkata"],
            "Mumbai": ["Delhi", "Goa", "Chennai"],
            "Bangalore": ["Delhi", "Chennai"],
            "Kolkata": ["Delhi"],
            "Goa": ["Mumbai"],
            "Chennai": ["Mumbai", "Bangalore"]
        }

    def list_options(self, origin):
        return self.paths.get(origin, [])

# Account Handler
class AccountHandler:
    def signup(self, account_name, passcode):
        try:
            result = travel_system.table("users").select("username").eq("username", account_name).execute()
            if result.data:
                return False, "Username already taken."
            travel_system.table("users").insert({"username": account_name, "password": passcode}).execute()
            return True, "Signup successful!"
        except Exception as e:
            return False, f"Signup error: {str(e)}"

    def verify(self, account_name, passcode):
        try:
            result = travel_system.table("users").select("password").eq("username", account_name).execute()
            if result.data and result.data[0]["password"] == passcode:
                return True
            return False
        except Exception as e:
            st.error(f"Verification error: {str(e)}")
            return False

# Streamlit App
def main():
    st.title("Adventure Planner System")
    
    # Session State Initialization
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
        st.session_state.user_id = ""
        st.session_state.travel_coordinator = None
        st.session_state.travel_list = TravelQueue()
    
    account_system = AccountHandler()
    route_system = RoutePlanner()
    valid_cities = list(route_system.paths.keys())
    valid_hotels = ["Taj Palace", "Oberoi", "ITC Grand", "Hyatt"]
    valid_packages = ["Goa Getaway", "Kerala Bliss", "Rajasthan Royals", "Himalayan Trek"]

    # Sidebar Navigation
    if not st.session_state.authenticated:
        page = st.sidebar.selectbox("Choose an option", ["Sign In", "Sign Up", "Exit"])
    else:
        page = st.sidebar.selectbox("Choose an option", ["Plan Trip", "Check Plans", "Find Plan", "Cancel Plan", "View Trends", "Sign Out", "Exit"])

    # Pages
    if page == "Sign In" and not st.session_state.authenticated:
        st.header("Sign In")
        user_id = st.text_input("Username")
        passcode = st.text_input("Password", type="password")
        if st.button("Sign In"):
            if not user_id or not passcode:
                st.error("Username and password cannot be empty.")
            elif account_system.verify(user_id, passcode):
                st.session_state.authenticated = True
                st.session_state.user_id = user_id
                st.session_state.travel_coordinator = TravelOrganizer(user_id)
                st.success(f"Welcome, {user_id}!")
            else:
                st.error("Incorrect username or password.")

    elif page == "Sign Up" and not st.session_state.authenticated:
        st.header("Sign Up")
        user_id = st.text_input("New Username")
        passcode = st.text_input("New Password", type="password")
        if st.button("Sign Up"):
            if not user_id or not passcode:
                st.error("Username and password cannot be empty.")
            else:
                success, message = account_system.signup(user_id, passcode)
                if success:
                    st.success(message)
                else:
                    st.error(message)

    elif page == "Plan Trip" and st.session_state.authenticated:
        st.header("Plan a Trip")
        trip_type = st.selectbox("Trip Type", ["Flight", "Hotel", "Package"])
        trip_date = st.date_input("Trip Date", min_value=datetime.today())

        if trip_type == "Flight":
            start_city = st.selectbox("Starting City", valid_cities)
            options = route_system.list_options(start_city)
            end_city = st.selectbox("Destination City", options)
            traveler_count = st.number_input("Number of Passengers", min_value=1, max_value=10, value=1)
            if traveler_count > 1:
                st.subheader("Passenger Details")
                traveler_info = []
                for i in range(traveler_count):
                    name = st.text_input(f"Passenger {i+1} Name")
                    age = st.number_input(f"Passenger {i+1} Age", min_value=0, value=0)
                    if name and age:
                        traveler_info.append({"name": name, "age": str(age)})
            else:
                traveler_info = []
            payment = st.selectbox("Payment Method", ["Credit", "Debit", "UPI"])
            if st.button("Book Flight"):
                plan = PlaneTravel(st.session_state.user_id, start_city, end_city, str(trip_date), traveler_count)
                plan.traveler_info = traveler_info
                if st.session_state.travel_coordinator.store_plan(plan):
                    st.session_state.travel_list.add(plan)
                    st.success(f"Flight booked! ID: {plan.plan_code}")
                else:
                    st.error("Failed to book flight.")

        elif trip_type == "Hotel":
            stay_name = st.selectbox("Hotel", valid_hotels)
            stay_duration = st.number_input("Number of Nights", min_value=1, max_value=30, value=1)
            group_size = st.number_input("Number of Persons", min_value=1, max_value=10, value=1)
            if group_size > 1:
                st.subheader("Guest Details")
                traveler_info = []
                for i in range(group_size):
                    name = st.text_input(f"Guest {i+1} Name")
                    age = st.number_input(f"Guest {i+1} Age", min_value=0, value=0)
                    if name and age:
                        traveler_info.append({"name": name, "age": str(age)})
            else:
                traveler_info = []
            payment = st.selectbox("Payment Method", ["Credit", "Debit", "UPI"])
            if st.button("Book Hotel"):
                plan = StayTravel(st.session_state.user_id, stay_name, str(trip_date), stay_duration)
                plan.traveler_info = traveler_info
                if st.session_state.travel_coordinator.store_plan(plan):
                    st.session_state.travel_list.add(plan)
                    st.success(f"Hotel booked! ID: {plan.plan_code}")
                else:
                    st.error("Failed to book hotel.")

        elif trip_type == "Package":
            adventure_title = st.selectbox("Package", valid_packages)
            group_size = st.number_input("Number of Persons", min_value=1, max_value=20, value=1)
            if group_size > 1:
                st.subheader("Group Details")
                traveler_info = []
                for i in range(group_size):
                    name = st.text_input(f"Person {i+1} Name")
                    age = st.number_input(f"Person {i+1} Age", min_value=0, value=0)
                    if name and age:
                        traveler_info.append({"name": name, "age": str(age)})
            else:
                traveler_info = []
            payment = st.selectbox("Payment Method", ["Credit", "Debit", "UPI"])
            if st.button("Book Package"):
                plan = AdventureTravel(st.session_state.user_id, adventure_title, str(trip_date), group_size)
                plan.traveler_info = traveler_info
                if st.session_state.travel_coordinator.store_plan(plan):
                    st.session_state.travel_list.add(plan)
                    st.success(f"Package booked! ID: {plan.plan_code}")
                else:
                    st.error("Failed to book package.")

    elif page == "Check Plans" and st.session_state.authenticated:
        st.header("Your Plans")
        plans = st.session_state.travel_coordinator.retrieve_plans()
        st.text_area("Plans", plans, height=300)

    elif page == "Find Plan" and st.session_state.authenticated:
        st.header("Find a Plan")
        plan_code = st.text_input("Enter Plan ID")
        if st.button("Search"):
            if not plan_code:
                st.error("Plan ID cannot be empty.")
            else:
                result = st.session_state.travel_coordinator.find_plan(plan_code)
                st.text_area("Search Result", result, height=200)

    elif page == "Cancel Plan" and st.session_state.authenticated:
        st.header("Cancel a Plan")
        plan_code = st.text_input("Enter Plan ID")
        cancel_option = st.radio("Cancel Option", ["Cancel Entire Plan", "Remove One Traveler"])
        if cancel_option == "Remove One Traveler":
            traveler_name = st.text_input("Enter Traveler Name to Remove")
        else:
            traveler_name = None
        if st.button("Cancel"):
            if not plan_code:
                st.error("Plan ID cannot be empty.")
            elif cancel_option == "Remove One Traveler" and not traveler_name:
                st.error("Traveler name cannot be empty.")
            else:
                if st.session_state.travel_coordinator.cancel_plan(plan_code, traveler_name):
                    if traveler_name:
                        st.success(f"Removed {traveler_name} from plan {plan_code}")
                    else:
                        st.success(f"Plan {plan_code} cancelled.")
                else:
                    st.error("Cancellation failed.")

    elif page == "View Trends" and st.session_state.authenticated:
        st.header("Travel Trends")
        fig = st.session_state.travel_coordinator.show_trends()
        st.pyplot(fig)

    elif page == "Sign Out" and st.session_state.authenticated:
        st.header("Sign Out")
        if st.button("Confirm Sign Out"):
            if st.session_state.travel_coordinator.end_session():
                st.success("Signed out and plans archived.")
            else:
                st.success("Signed out (no plans to archive).")
            st.session_state.authenticated = False
            st.session_state.user_id = ""
            st.session_state.travel_coordinator = None
            st.session_state.travel_list.reset()

    elif page == "Exit":
        st.header("Exit Application")
        if st.button("Confirm Exit"):
            # Reset session state regardless of authentication status
            if st.session_state.authenticated and st.session_state.travel_coordinator:
                st.session_state.travel_coordinator.end_session()  # Archive plans if authenticated
            st.session_state.authenticated = False
            st.session_state.user_id = ""
            st.session_state.travel_coordinator = None
            st.session_state.travel_list.reset()
            st.info("Application exited. You can close this tab.")
            # Optional: Stops the Streamlit server (works locally, not in cloud)
            # os._exit(0)

if __name__ == "__main__":
    main()