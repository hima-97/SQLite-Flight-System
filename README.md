# Project Description

This project consists of the following parts:
- Design and implement an SQLite database for a flight booking service
- Build a working prototype of the flight booking application that connects to the SQLite database and allows customers to use a CLI to search, book, cancel, etc. flights

# Implementation Details

The project uses [SQLite](https://www.sqlite.org/index.html) through [Python apsw library](https://rogerbinns.github.io/apsw/index.html) for the database management. <br>
The project uses Python for the application that the customers use.

The code for the UI is in the `FlightService.py` file. <br>
The code for the backend is in the `Query.py` file.

The flight service system consists of the following logical entities (these entities are *not necessarily database tables*):

**Flights / Carriers / Months / Weekdays** <br>
The application has limited functionality, so no additional tables should be needed.

**Users** <br>
A user has a username (`varchar`), password (`varbinary`), and balance (`int`) in their account.
All usernames should be unique in the system. Each user can have any number of reservations.
Usernames are case insensitive (this is the default for SQLite).
You can assume that all usernames and passwords have at most 20 characters.

**Itineraries** <br>
An itinerary is either a direct flight (consisting of one flight: origin --> destination) or<br>
a one-hop flight (consisting of two flights: origin --> stopover city, stopover city --> destination). <br>
Itineraries are returned by the search command.

**Reservations**<br>
A booking for an itinerary, which may consist of one (direct) or two (one-hop) flights.<br>
Each reservation can either be paid or unpaid, cancelled or not, and has a unique ID.

**ReservationsId**<br>
Used for obtaining atomically increasing reservation ID.

--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

The program allows the user to perform the following commands:
- `create <username> <password> <initial amount>` <br>`
Function that takes in a new username, password, and initial account balance as input, and then creates a new user account with the initial balance. <br>
It should return an error if negative, or if the username already exists. Usernames are checked case-insensitively. <br>
You can assume that all usernames and passwords have at most 20 characters.

- `login <username> <password>` <br>
Function that takes in a username and password, checks that the user exists in the database and that the password matches. <br>
Within a single session (that is, a single instance of program), only one user should be logged in (tracked this via a local variable). <br>
If a second login attempt is made, program returns "User already logged in". <br>
Across multiple sessions (that is, if you run program multiple times), the same user is allowed to be logged in. <br>
This means that a user's login status is not needed to be tracked inside the database.

- `search <origin city> <destination city> <direct> <day> <num itineraries>` <br>
For the date, we only need the day of the month, since the dataset comes from July 2015. <br>
Program returns only flights that are not canceled, ignoring the capacity and number of seats available. <br>
If the user requests n itineraries to be returned, there are a number of possibilities:
  - direct=1: return up to n direct itineraries
  - direct=0: return up to n direct itineraries. If there are only k direct itineraries (where k < n), find the k direct itineraries and up to (n-k) of the shortest indirect itineraries with the flight times. Then sort the combinations of direct and indirect flights purely based on the total travel time. For one-hop flights, different carriers can be used for the flights. For the purpose of this application, an indirect itinerary means the first and second flight only must be on the same date (i.e., if flight 1 runs on the 3rd day of July, flight 2 runs on the 4th day of July, then you can't put these two flights in the same itinerary as they are not on the same day). <br>
In all cases, the returned results should be primarily sorted by ascending total actual_time (there could be some indirect flights have less total travel time less than the direct flight).<br>
If a tie occurs, it is broken by the fid value (i.e. use the first then the second fid for tie-breaking).

  Below is an example of a single direct flight from Seattle to Boston. <br>
  Notice that only the day is printed out since we assume all flights happen in July 2015: <br>

  ```
  Itinerary 0: 1 flight(s), 297 minutes
  ID: 60454 Day: 1 Carrier: AS Number: 24 Origin: Seattle WA Dest: Boston MA Duration: 297 Capacity: 14 Price: 140
  ```

  Below is an example of two indirect flights from Seattle to Boston: <br>

  ```
  Itinerary 0: 2 flight(s), 317 minutes
  ID: 704749 Day: 10 Carrier: AS Number: 16 Origin: Seattle WA Dest: Orlando FL Duration: 159 Capacity: 10 Price: 494
  ID: 726309 Day: 10 Carrier: B6 Number: 152 Origin: Orlando FL Dest: Boston MA Duration: 158 Capacity: 0 Price: 104
  Itinerary 1: 2 flight(s), 317 minutes
  ID: 704749 Day: 10 Carrier: AS Number: 16 Origin: Seattle WA Dest: Orlando FL Duration: 159 Capacity: 10 Price: 494
  ID: 726464 Day: 10 Carrier: B6 Number: 452 Origin: Orlando FL Dest: Boston MA Duration: 158 Capacity: 7 Price: 760
  ```

  Note that for one-hop flights, the results are printed in the order of the itinerary, starting from the flight leaving the origin and ending with the flight arriving at the destination. <br>
  Moreover, the user need not be logged in to search for flights. <br>
  All flights in an indirect itinerary should be under the same itinerary ID. In other words, the user should only need to book once with the itinerary ID for direct or indirect trips.

- `book <itinerary id>` <br>
Function that lets a user book an itinerary by providing the itinerary number as returned by a previous search. <br>
The user must be logged in to book an itinerary, and must enter a valid itinerary id that was returned in the last search that was performed *within the same login session*. <br>
Make sure you make the corresponding changes to the tables in case of a successful booking. <br>
When the user logs out (by quitting the application), logs in (if they previously were not logged in), or performs another search within the same login session, then all previously returned itineraries are invalidated and cannot be booked. <br>
A user cannot book a flight if the flight's maximum capacity would be exceeded and there should be records as to how many seats remain on each flight based on the reservations. <br>
If booking is successful, then assign a new reservation ID to the booked itinerary. <br>
Each reservation can contain up to 2 flights (in the case of indirect flights). <br>
Each reservation should have a unique ID that incrementally increases by 1 for each successful booking.

- `pay <reservation id>` <br>
Function that allows a user to pay for an existing unpaid reservation. <br>
It first checks whether the user has enough money to pay for all the flights in the given reservation. <br>
If successful, it updates the reservation to be paid.

- `reservations` <br>
Function that lists all reservations for the currently logged-in user. <br>
Each reservation has ***a unique identifier (which is different for each itinerary) in the entire system***, starting from 1 and increasing by 1 after each reservation is made. <br>
There are many ways to implement this. One possibility is to define a "ID" table that stores the next ID to use, and update it each time when a new reservation is made successfully. <br>
The itineraries should be displayed using similar format as that used to display the search results, and they should be shown in increasing order of reservation ID under that username. <br>
A customer may have at most one reservation on any given day, but they can be on more than 1 flight on the same day (i.e., a customer can have one reservation on a given day that includes two flights, because the reservation is for a one-hop itinerary). <br>
The user must be logged in to view reservations and cancelled reservations should not be displayed.

- `cancel <reservation id>` <br>
Function that lets a user cancel an existing uncanceled reservation. The user must be logged in to cancel reservations and must provide a valid reservation ID. <br>
Make sure you make the corresponding changes to the tables in case of a successful cancellation (e.g., if a reservation is already paid, then the customer should be refunded).

- `quit` <br>
Function that leaves the interactive system and logs out the current user (if logged in). <br>

Note: while implementing and trying out these commands, there are problems when multiple users try to use the service concurrently. <br>
To resolve this challenge, you will need to implement transactions that ensure concurrent commands do not conflict.

Note: transactions must be used correctly such that race conditions introduced by concurrent execution cannot lead to an inconsistent state of the database. <br>
For example, multiple customers may try to book the same flight at the same time.

Note: avoid including user interaction inside a SQL transaction (i.e. don't be in a transaction then wait for the user to decide what to do). The rule of thumb is that transactions need to be *as short as possible, but not shorter*.

Note: when one uses a DBMS, recall that by default each statement executes in its own transaction.<br>
This is the same when executing transactions from Python (each SQL statement will be executed as its own transaction). <br>

Note: the `executeQuery` calls will throw a `SQLException` when an error occurs (e.g., multiple customers try to book the same flight concurrently). It's important to handle such exception appropriately. For instance, if a seat is still available but the execution failed due a temporary issue such as deadlock, the booking should eventually go through (even though you might need to retry due to `SQLException`s being thrown).

Note: each user starts concurrently in the beginning and if there are multiple output possibilities due to transactional behavior, then each group of expected output is separated with `|`.

# Tools and Concepts

- Languages: Python, SQL
- VSCode
- Database application development
- Transaction management

# Running and Testing the Project

You can run and test the project by running the following command:

- `python testing.py`

- Note: the script in the `testing.py` file is used to run all the test cases in the `Test Cases` folder

- Note: for all failed cases, the program will dump out what the implementation returned

Each test case file is of the following format:

```sh
[command 1]
[command 2]
...
*
[expected output line 1]
[expected output line 2]
...
*
```

The `*` separates between commands and the expected output. To test with multiple concurrent users, simply add more `[command...] * [expected output...]` pairs to the file, for instance:

 ```sh
 [command 1 for user1]
 [command 2 for user1]
 ...
 *
 [expected output line 1 for user1]
 [expected output line 2 for user1]
 ...
 *
 [command 1 for user2]
 [command 2 for user2]
 ...
 *
 [expected output line 1 for user2]
 [expected output line 2 for user2]
 ...
 *
 ```