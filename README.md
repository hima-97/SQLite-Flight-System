# Flight Booking System

## Project Overview

This project involves the design and implementation of a flight booking service using SQLite and Python. The key components of the project include:

1. Designing and implementing an SQLite database for managing flight bookings.
2. Building a CLI-based flight booking application that connects to the SQLite database and allows users to perform various operations such as searching for flights, booking, canceling, and managing reservations.

## Implementation Details

### Technology Stack

- **Database**: SQLite (using the APSW library in Python)
- **Programming Language**: Python
- **Development Environment**: VSCode

### Code Structure

- `FlightService.py`: Contains the code for the user interface (CLI) and command handling.
- `Query.py`: Contains the backend code for database interactions and transaction management.

### Logical Entities

1. **Flights / Carriers / Months / Weekdays**: Basic entities for storing flight information.
2. **Users**: Each user has a unique username, a password, and an account balance.
3. **Itineraries**: Can be either direct flights or one-hop flights (involving a stopover).
4. **Reservations**: Represent bookings made by users, which can include one or two flights.
5. **ReservationsId**: Manages unique reservation IDs for bookings.

### Database Schema

The database schema includes tables for `Carriers`, `Months`, `Weekdays`, `Flights`, `Customers`, `Itineraries`, `Reservations`, and `ReservationsId`. The schema is created and managed within the `Query.py` file.

## Commands and Operations

### User Commands

1. **Create User**
   - `create <username> <password> <initial amount>`
   - Creates a new user account with the specified username, password, and initial balance.

2. **Login**
   - `login <username> <password>`
   - Logs in a user if the provided credentials match an existing user.

3. **Search Flights**
   - `search <origin city> <destination city> <direct> <day> <num itineraries>`
   - Searches for flights between the specified origin and destination cities on the given day. Can search for direct or indirect flights.

4. **Book Flight**
   - `book <itinerary id>`
   - Books an itinerary (flight) based on the ID returned from a previous search.

5. **Pay for Reservation**
   - `pay <reservation id>`
   - Allows a user to pay for an existing unpaid reservation.

6. **View Reservations**
   - `reservations`
   - Lists all reservations for the currently logged-in user.

7. **Cancel Reservation**
   - `cancel <reservation id>`
   - Cancels an existing reservation.

8. **Quit**
   - `quit`
   - Exits the application and logs out the current user.

### Transaction Management

- Transactions ensure data consistency and handle race conditions when multiple users interact with the system concurrently.
- Proper transaction handling is implemented to avoid issues like deadlocks and to ensure the correct execution of concurrent commands.

## Testing and Running the Project

### Running the Project

To run the project, execute the following command:
```sh
python testing.py
```

### Test Cases

The test cases are located in the `Test Cases` folder and are structured to test both concurrent and non-concurrent scenarios.

Each test case file follows this format:
```sh
[command 1]
[command 2]
...
*
[expected output line 1]
[expected output line 2]
...
*

For testing multiple concurrent users, additional [command...] * [expected output...] pairs can be added to the test case file.

Example Test Case
elow is an example of a test case for booking the same flight by two users concurrently
# user 1
create user1 user1 10000
login user1 user1
search "Kahului HI" "Los Angeles CA" 0 6 1
book 0
quit
*
# expected printouts for user 1
Created user user1
Logged in as user1
Itinerary 0: 1 flight(s), 273 minutes
ID: 131239 Day: 6 Carrier: DL Number: 292 Origin: Kahului HI Dest: Los Angeles CA Duration: 273 Capacity: 14 Price: 689
Booked flight(s), reservation ID: 2
Goodbye
|
Created user user1
Logged in as user1
Itinerary 0: 1 flight(s), 273 minutes
ID: 131239 Day: 6 Carrier: DL Number: 292 Origin: Kahului HI Dest: Los Angeles CA Duration: 273 Capacity: 14 Price: 689
Booked flight(s), reservation ID: 1
Goodbye
*
# user 2
create user2 user2 10000
login user2 user2
search "Kahului HI" "Los Angeles CA" 0 6 1
book 0
quit
*
# expected printouts for user 2
Created user user2
Logged in as user2
Itinerary 0: 1 flight(s), 273 minutes
ID: 131239 Day: 6 Carrier: DL Number: 292 Origin: Kahului HI Dest: Los Angeles CA Duration: 273 Capacity: 14 Price: 689
Booked flight(s), reservation ID: 1
Goodbye
|
Created user user2
Logged in as user2
Itinerary 0: 1 flight(s), 273 minutes
ID: 131239 Day: 6 Carrier: DL Number: 292 Origin: Kahului HI Dest: Los Angeles CA Duration: 273 Capacity: 14 Price: 689
Booked flight(s), reservation ID: 2
Goodbye
*
```