import sqlite3

conn = sqlite3.connect('Checkpoint2-dbase.sqlite3')
cursor = conn.cursor()

def delete_route_and_save(route_id):
    # Save the route to the temporary table before deleting
    cursor.execute("""
        INSERT INTO deleted_routes (route_id, route_name, start_loc)
        SELECT route_id, route_name, start_loc
        FROM routes
        WHERE route_id = ?;
    """, (route_id,))
    conn.commit()

    # Delete the route from the routes table
    cursor.execute("DELETE FROM routes WHERE route_id = ?;", (route_id,))
    conn.commit()
    return f"Route {route_id} has been deleted and saved for potential undo."

def undo_delete_route(route_id):
    # Restore the route from the temporary table
    cursor.execute("""
        INSERT INTO routes (route_id, route_name, start_loc)
        SELECT route_id, route_name, start_loc
        FROM deleted_routes
        WHERE route_id = ?;
    """, (route_id,))
    conn.commit()

    # Remove the restored route from the temporary table
    cursor.execute("DELETE FROM deleted_routes WHERE route_id = ?;", (route_id,))
    conn.commit()
    return f"Route {route_id} has been restored."

def view_bus_schedule(departure_date, route_name):
    query = """
    SELECT schedules.departure_time, buses.bus_number, routes.route_name
    FROM schedules
    JOIN buses ON schedules.bus_id = buses.bus_id
    JOIN routes ON schedules.route_id = routes.route_id
    WHERE routes.route_name = ? AND DATE(schedules.departure_time) = ?
    ORDER BY schedules.departure_time;
    """
    cursor.execute(query, (route_name, departure_date))
    return cursor.fetchall()

def plan_trip(bus_number, route_name, departure_time):
    query = f"SELECT bus_id FROM buses WHERE bus_number = '{bus_number}'"
    cursor.execute(query)
    bus_id = cursor.fetchone()

    query = f"SELECT route_id FROM routes WHERE route_name = '{route_name}'"
    cursor.execute(query)
    route_id = cursor.fetchone()

    if bus_id and route_id:
        bus_id = bus_id[0]
        route_id = route_id[0]
        query = f"INSERT INTO schedules (departure_time, bus_id, route_id) VALUES ('{departure_time}', {bus_id}, {route_id})"
        cursor.execute(query)
        conn.commit()
        return f"Trip planned successfully with Bus Number: {bus_number}, Route: {route_name}, Departure Time: {departure_time}"
    else:
        return "Invalid bus number or route name."
    
def check_bus_status(bus_id=None, bus_number=None):
    if bus_id:
        query = "SELECT bus_status FROM buses WHERE bus_id = ?;"
        cursor.execute(query, (bus_id,))
    elif bus_number:
        query = "SELECT bus_status FROM buses WHERE bus_number = ?;"
        cursor.execute(query, (bus_number,))
    else:
        return "Please provide a valid Bus ID or Bus Number."

    result = cursor.fetchone()
    if result:
        return f"Bus Status: {result[0]}"
    else:
        return "Bus not found."

def view_user_tickets(user_id):
    query = """
        SELECT t.ticket_id, t.trip_date, t.price, r.route_name
        FROM tickets t
        JOIN routes r ON t.route_id = r.route_id
        WHERE t.user_id = ?;
    """
    cursor.execute(query, (user_id,))
    results = cursor.fetchall()
    if results:
        return [f"Ticket ID: {row[0]}, Trip Date: {row[1]}, Price: ${row[2]:.2f}, Route: {row[3]}" for row in results]
    else:
        return "No tickets found for this user."

def delete_route(route_id):
    cursor.execute('DELETE FROM routes WHERE route_id = ?;', (route_id,))
    conn.commit()
    cursor.execute("SELECT * FROM routes WHERE route_id = ?", (route_id,))
    return cursor.fetchone() is None

def fare_per_bus(user_id, trip_date):
    cursor.execute('SELECT price FROM tickets WHERE user_id = ? AND date(trip_date) = ?;', (user_id, trip_date))
    return cursor.fetchone()

def total_fare(user_id):
    cursor.execute('SELECT SUM(price) as total_fare FROM tickets WHERE user_id = ?;', (user_id,))
    return cursor.fetchone()

def manage_bus_status(bus_id, bus_status):
    cursor.execute('UPDATE buses SET bus_status = ? WHERE bus_id = ?;', (bus_status, bus_id))
    conn.commit()

def update_bus_number(bus_id, bus_number):
    cursor.execute('UPDATE buses SET bus_number = ? WHERE bus_id = ?;', (bus_number, bus_id))
    conn.commit()

def manage_route(route_id, new_route_name):
    cursor.execute('UPDATE routes SET route_name = ? WHERE route_id = ?;', (new_route_name, route_id))
    conn.commit()

def main():
    user_type = input("Is this an admin or a user? Select 1 for user and 2 for admin: ")

    if user_type == "2":
        password = input("Please input the password for admin: ")
        if password != "the password":
            print("Invalid Password! Ending the program...")
            return
        print("Password Admitted! Welcome admin!")

    while True:
        if user_type == "1":
            print("\nMenu:")
            print("1. View Bus Schedule")
            print("2. Check Fare for a Trip")
            print("3. Calculate Total Fare")
            print("4. Check Bus Status")
            print("5. Check Tickets")
            print("6. Exit")
            choice = input("Welcome user! What would you like to do? ")
            if choice == "1":
                route_name = input("Enter the route name: ")
                departure_date = input("Enter the departure date (YYYY-MM-DD): ")
                schedule = view_bus_schedule(departure_date, route_name)
                if schedule:
                    print(f"Bus Schedule for {route_name} on {departure_date}:")
                    for row in schedule:
                        print(row)
                else:
                    print(f"No buses scheduled for {route_name} on {departure_date}.")
            elif choice == "2":
                user_id = input("Enter your user ID: ")
                trip_date = input("Enter the trip date (YYYY-MM-DD): ")
                fare = fare_per_bus(user_id, trip_date)
                if fare:
                    print(f"The fare for User {user_id} on {trip_date} is: ${fare[0]}")
                else:
                    print(f"No fare found for User {user_id} on {trip_date}.")
            elif choice == "3":
                user_id = input("Enter your user ID: ")
                total = total_fare(user_id)
                if total and total[0]:
                    print(f"Total fare spent by User {user_id}: ${total[0]}")
                else:
                    print(f"No fare records found for User {user_id}.")
            elif choice == "4":
                search_by = input("Search by (1) Bus ID or (2) Bus Number? ")
                if search_by == "1":
                    bus_id = input("Enter the Bus ID: ")
                    print(check_bus_status(bus_id=bus_id))
                elif search_by == "2":
                    bus_number = input("Enter the Bus Number: ")
                    print(check_bus_status(bus_number=bus_number))
                else:
                    print("Invalid option. Please choose either 1 or 2.")
            elif choice == "5":
                user_id = input("Enter User ID: ")
                tickets = view_user_tickets(user_id)
                if isinstance(tickets, list):
                    print("\nUser Ticket History:")
                    for ticket in tickets:
                        print(ticket)
                else:
                    print("\n", tickets)
            elif choice == "6":
                print("Goodbye!")
                break
            else:
                print("Invalid choice. Please try again.")

        elif user_type == "2":
            print("\nMenu:")
            print("1. Delete a Route") 
            print("2. Undo Delete Route") 
            print("3. Manage Bus Status") 
            print("4. Update Bus Number") 
            print("5. Manage Route Name") 
            print("6. Create a New Schedule")
            print("7. Exit")
            choice = input("Welcome admin! What would you like to do? ")

            if choice == "1":
                route_id = input("Enter the route ID to delete: ")
                print(delete_route_and_save(route_id))    
            elif choice == "2":
                route_id = input("Enter the route ID to restore: ")
                print(undo_delete_route(route_id))
            elif choice == "3":
                bus_id = input("Enter the bus ID: ")
                bus_status = input("Enter the new bus status (e.g., 'in service', 'out of service', 'delayed'): ")
                manage_bus_status(bus_id, bus_status)
                print(f"Bus {bus_id} status updated to {bus_status}.")
            elif choice == "4":
                bus_id = input("Enter the bus ID: ")
                bus_number = input("Enter the new bus number: ")
                update_bus_number(bus_id, bus_number)
                print(f"Bus {bus_id} number updated to {bus_number}.")
            elif choice == "5":
                route_id = input("Enter the route ID: ")
                new_route_name = input("Enter the new route name: ")
                manage_route(route_id, new_route_name)
                print(f"Route {route_id} name updated to {new_route_name}.")
            elif choice == "6":
                bus_number = input("Enter the bus number: ")
                route_name = input("Enter the route name: ")
                departure_time = input("Enter the departure time (YYYY-MM-DD HH:MM:SS): ")
                print(plan_trip(bus_number, route_name, departure_time))
            elif choice == "7":
                print("Goodbye!")
                break
            else:
                print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()


