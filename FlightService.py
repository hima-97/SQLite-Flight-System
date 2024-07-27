import Query  # Importing the Query module which contains the backend logic for the application
import re  # Importing the re module for regular expressions

def filter_empty(tokens):
    """
    Filters out empty tokens from the list and returns the first non-empty token.
    Args:
    - tokens: List of tokens (strings)
    Returns:
    - results: List of non-empty tokens
    """
    results = []
    for token in tokens:
        results.append(list(filter(None, token))[0])  # Filter out empty tokens and append the first non-empty token
    return results

def execute(q, command):
    """
    Executes a given command by calling the appropriate transaction function in the Query module.
    Args:
    - q: Query object that handles database transactions
    - command: Command string input by the user
    Returns:
    - response: Response string to be printed or returned
    """
    response = ""
    regex = "\"([^\"]*)\"|(\\S+)"  # Regular expression to match quoted strings or non-whitespace sequences
    tokens = filter_empty(re.findall(regex, command))  # Tokenize the command string using the regex
    if(len(tokens) == 0):
        response = "Please enter a command"
    elif(tokens[0] == "login"):
        if(len(tokens) == 3):
            username = tokens[1]
            password = tokens[2]
            response = q.transactionLogin(username, password)  # Call login transaction
        else:
            response = "Error: Please provide a username and password"
    elif(tokens[0] == "create"):
        if(len(tokens) == 4):
            username = tokens[1]
            password = tokens[2]
            initAmount = int(tokens[3])
            response = q.transactionCreateCustomer(username, password, initAmount)  # Call create customer transaction
        else:
            response = "Error: Please provide a username, password, and initial amount in the account"
    elif(tokens[0] == "search"):
        if(len(tokens) == 6):
            originCity = tokens[1]
            destCity = tokens[2]
            direct = tokens[3] == "1"  # Convert to boolean
            try:
                day = int(tokens[4])
                count = int(tokens[5])
                response = q.transactionSearch(originCity, destCity, direct, day, count)  # Call search transaction
            except ValueError:
                response = "Failed to parse integer"
        else:
            response = "Error: Please provide all search parameters <origin_city> <destination_city> <direct> <date> <nb itineraries>"
    elif(tokens[0] == "book"):
        if(len(tokens) == 2):
            itinerarayId = int(tokens[1])
            response = q.transactionBook(itinerarayId)  # Call book transaction
        else:
            response = "Error: Please provide an itinerary_id"
    elif(tokens[0] == "reservations"):
        response = q.transactionReservation()  # Call reservations transaction
    elif(tokens[0] == "pay"):
        if(len(tokens) == 2):
            reservationId = int(tokens[1])
            response = q.transactionPay(reservationId)  # Call pay transaction
        else:
            response = "Error: Please provide a reservation_id"
    elif(tokens[0] == "cancel"):
        if(len(tokens) == 2):
            reservationId = int(tokens[1])
            response = q.transactionCancel(reservationId)  # Call cancel transaction
        else:
            response = "Error: Please provide a reservation_id"
    elif(tokens[0] == "quit"):
        q.conn.close()  # Close the database connection
        response = "Goodbye\n"
    elif(tokens[0] == "SQL"):
        print(q.conn.cursor().execute(tokens[1]).fetchall())  # Execute raw SQL command (for debugging/testing)
    else:
        response = "Error: unrecognized command '{}'".format(tokens[0])

    return response

def menu(q):
    """
    Displays a menu of commands and processes user input in a loop.
    Args:
    - q: Query object that handles database transactions
    """
    while(True):
        print(" *** Please enter one of the following commands *** ")
        print("> create|<username>|<password>|<initial amount>")
        print("> login|<username>|<password>")
        print("> search|<origin city>|<destination city>|<direct>|<day of the month>|<num itineraries>")
        print("> book|<itinerary id>")
        print("> pay|<reservation id>")
        print("> reservations")
        print("> cancel|<reservation id>")
        print("> quit")
        command = input("> enter your command here : ")
        response = execute(q, command)  # Execute the command
        print(response)
        if(response == "Goodbye\n"):  # Exit loop if quit command is given
            break

def main():
    """
    Main function to start the flight service application.
    """
    q = Query.Query()  # Create a Query object to handle database transactions
    menu(q)  # Start the menu loop
    q.closeConnection()  # Close the database connection

if __name__ == "__main__":
    main()  # Run the main function if this script is executed directly
