# Himanshu Kumar
import sqlite3
import subprocess
import os
import csv
import apsw
import time

DB_NAME = "example.db"


def busyHandlerCallback(retryCount):
    if retryCount <= 5:
        time.sleep(5**retryCount)
        return 5000
    else:
        False


# A class to store flight information.
class Flight:
    def __init__(self, fid = -1, dayOfMonth=0, carrierId=0, flightNum=0, originCity="", destCity="", time=0, capacity=0, price=0):
        self.fid = fid
        self.dayOfMonth = dayOfMonth
        self.carrierId = carrierId
        self.flightNum = flightNum
        self.originCity = originCity
        self.destCity = destCity
        self.time = time
        self.capacity = capacity
        self.price = price

    def toString(self):
        return "ID: {} Day: {} Carrier: {} Number: {} Origin: {} Dest: {} Duration: {} Capacity: {} Price: {}\n".format(
                self.fid, self.dayOfMonth, self.carrierId, self.flightNum, self.originCity, self.destCity,self.time, self.capacity, self.price)


class Itinerary:
    #one-hop flight
    def __init__(self,  time ,flight1, flight2=Flight()):# the second one could be empty flight
        self.flights=[]
        self.flights.append(flight1)
        self.flights.append(flight2)
        self.time = time

    
    def itineraryPrice(self):
        price = 0
        for f in self.flights:
            price += f.price
        return price

    def numFlights(self):
        if(self.flights[1].fid == -1):
            return 1
        else:
            return 2

    def toString(self):
        the_string = "{} flight(s), {} minutes\n".format(self.numFlights(), self.time)
        for i in range(self.numFlights()):
            the_string += self.flights[i].toString()
        return the_string


class Reservation:
    def __init__(self, rid, paid, flight1, flight2=Flight()):  # the second one could be empty flight
        self.flights = []
        self.flights.append(flight1)
        self.flights.append(flight2)
        self.rid = rid
        self.paid = paid

    def numFlights(self):
        if(self.flights[1].fid == -1):
            return 1
        else:
            return 2

    def isPaidStr(self):
        if self.paid == 1:
            return "true"
        else:
            return "false"

    def toString(self):
        the_string = "Reservation {} paid: {}:\n".format(self.rid, self.isPaidStr())
        for i in range(self.numFlights()):
            the_string += self.flights[i].toString()
        return the_string
    

class Query:
    CREATE_CUSTOMER_SQL = "INSERT INTO Customers VALUES('{}', '{}', {})"
    CUSTOMER_LOGIN_SQL = "SELECT username FROM Customers WHERE username = '{}' AND password = '{}'"

    DIRECT_FLIGHTS_SQL = """
    SELECT fid, day_of_month, carrier_id, flight_num, origin_city, dest_city, actual_time, capacity, price
    FROM Flights
    WHERE LOWER(origin_city) = '{}'
      AND LOWER(dest_city) = '{}'
      AND day_of_month = {}
      AND canceled = 0
    ORDER BY actual_time, fid
    LIMIT {}
    """
    INDIRECT_FLIGHTS_SQL = """
    SELECT F1.fid, F1.day_of_month, F1.carrier_id, F1.flight_num, F1.origin_city, F1.dest_city, F1.actual_time, F1.capacity, F1.price,
       F2.fid, F2.day_of_month, F2.carrier_id, F2.flight_num, F2.origin_city, F2.dest_city, F2.actual_time, F2.capacity, F2.price,
       F1.actual_time + F2.actual_time total_time
    FROM Flights F1, Flights F2
    WHERE LOWER(F1.origin_city) = '{}'
      AND LOWER(F2.dest_city) = '{}'
      AND F1.dest_city = F2.origin_city
      AND F1.day_of_month = F2.day_of_month
      AND F1.day_of_month = {}
      AND F1.canceled = 0
      AND F2.canceled = 0
    ORDER BY total_time, F1.fid, F2.fid
    LIMIT {}
    """

    SELECT_FLIGHT_SQL = "SELECT fid, day_of_month, carrier_id, flight_num, origin_city, dest_city, actual_time, capacity, price FROM Flights WHERE fid = {}"
    SELECT_RESERVATION_SQL = "SELECT rid, fid1, fid2, paid FROM Reservations WHERE username = '{}' AND canceled = 0"
    UPDATE_RESERVATION_ID_SQL = "UPDATE ReservationsId SET rid = rid + 1"
    CREATE_RESERVATION_SQL = """
    INSERT INTO Reservations
    SELECT rid, {}, {}, {}, {}, {}, '{}', {}
    FROM ReservationsId
    """
    CHECK_UNPAID_RESERVATION_SQL = "SELECT rid FROM Reservations WHERE rid = {} AND username = '{}' AND paid = 0"
    GET_BALANCE_SQL = "SELECT balance FROM Customers WHERE username = '{}'"
    GET_PRICE_SQL = "SELECT price FROM Reservations WHERE rid = {}"
    PAY_FOR_RESERVATION_SQL = "UPDATE Reservations SET paid = 1 WHERE rid = {}"
    UPDATE_BALANCE_SQL = "UPDATE Customers SET balance = {} WHERE username= '{}'"
    CANCEL_RESERVATION_SQL = "UPDATE Reservations SET canceled = 1 WHERE rid = {}"

    CHECK_FLIGHT_DAY = "SELECT * FROM Reservations r, Flights f WHERE r.username = '{}' AND f.day_of_month = {} AND r.fid1 = f.fid"
    CHECK_FLIGHT_CAPACITY = "SELECT capacity FROM Flights WHERE fid = {}"
    CHECK_BOOKED_SEATS = "SELECT COUNT(*) AS cnt FROM Reservations WHERE (fid1 = {} OR fid2 = {}) AND canceled = 0"
    CLEAR_DB_SQL1 = "DELETE FROM Reservations;"
    CLEAR_DB_SQL2 = "DELETE FROM Customers;"
    CLEAR_DB_SQL3 = "UPDATE ReservationsId SET rid = 1;"


    username = None
    lastItineraries = []
    reservations = []

    def __init__(self):
        self.db_name = DB_NAME
        self.conn = apsw.Connection(self.db_name, statementcachesize=0)
        self.conn.setbusytimeout(5000)
        self.conn.setbusyhandler(busyHandlerCallback)

    def startConnection(self):
        self.conn = apsw.Connection(self.db_name, statementcachesize=0)


    def closeConnection(self):
        self.conn.close()


    '''
    * Clear the data in any custom tables created. and reload the Carriers, Flights, Weekdays and Months tables.
    * 
    * WARNING! Do not drop any tables and do not clear the flights table.
    '''
    def clearTables(self):
        try:
            os.remove(DB_NAME)
            open(DB_NAME, 'w').close()
            os.system("chmod 777 {}".format(DB_NAME))
            # remove old db file
            # se sqlite3 example.db < create_tables.sql to reconstruct the db file. This can save many lines of code.
            # I have to reconstruct the db before each test
            self.conn = apsw.Connection(self.db_name, statementcachesize=0)

            self.conn.cursor().execute("PRAGMA foreign_keys=ON;")
            self.conn.cursor().execute(" PRAGMA serializable = true;")
            self.conn.cursor().execute("CREATE TABLE Carriers (cid VARCHAR(7) PRIMARY KEY, name VARCHAR(83))")
            self.conn.cursor().execute("""   
                    CREATE TABLE Months (
                        mid INT PRIMARY KEY,
                        month VARCHAR(9)
                    );""")

            self.conn.cursor().execute("""       
                    CREATE TABLE Weekdays(
                        did INT PRIMARY KEY,
                        day_of_week VARCHAR(9)
                    );""")
            self.conn.cursor().execute("""      
                    CREATE TABLE Flights (
                        fid INT PRIMARY KEY, 
                        month_id INT,        -- 1-12
                        day_of_month INT,    -- 1-31 
                        day_of_week_id INT,  -- 1-7, 1 = Monday, 2 = Tuesday, etc
                        carrier_id VARCHAR(7), 
                        flight_num INT,
                        origin_city VARCHAR(34), 
                        origin_state VARCHAR(47), 
                        dest_city VARCHAR(34), 
                        dest_state VARCHAR(46), 
                        departure_delay INT, -- in mins
                        taxi_out INT,        -- in mins
                        arrival_delay INT,   -- in mins
                        canceled INT,        -- 1 means canceled
                        actual_time INT,     -- in mins
                        distance INT,        -- in miles
                        capacity INT, 
                        price INT,           -- in $
                        FOREIGN KEY (carrier_id) REFERENCES Carriers(cid),
                        FOREIGN KEY (month_id) REFERENCES Months(mid),
                        FOREIGN KEY (day_of_week_id) REFERENCES Weekdays(did)
                    );""")
            self.conn.cursor().execute("""        
                    CREATE TABLE Customers(
                        username VARCHAR(256),
                        password VARCHAR(256),
                        balance INT,
                        PRIMARY KEY (username)
                    );""")
            self.conn.cursor().execute("""      
                    CREATE TABLE Itineraries(
                        direct INT, -- 1 or 0 stands for direct or one-hop flights
                        fid1 INT,
                        fid2 INT -- -1 means that this is a direct flight and has no second flight
                    );""")
            self.conn.cursor().execute("""      
                    CREATE TABLE Reservations(
                        rid INT,
                        price INT,
                        fid1 INT,
                        fid2 INT,
                        paid INT,
                        canceled INT,
                        username VARCHAR(256),
                        day_of_month INT,
                        PRIMARY KEY (rid)
                    );""")
            self.conn.cursor().execute("""      
                    CREATE TABLE ReservationsId(
                        rid INT
                    );""")

            self.conn.cursor().execute("INSERT INTO ReservationsId VALUES (1);")

            # reload db file for next tests

            with open("carriers.csv") as carriers:
                carriers_data = csv.reader(carriers)
                self.conn.cursor().executemany("INSERT INTO Carriers VALUES (?, ?)", carriers_data)

            with open("months.csv") as months:
                months_data = csv.reader(months)
                self.conn.cursor().executemany("INSERT INTO Months VALUES (?, ?)", months_data)

            with open("weekdays.csv") as weekdays:
                weekdays_data = csv.reader(weekdays)
                self.conn.cursor().executemany("INSERT INTO Weekdays VALUES (?, ?)", weekdays_data)
            
            #conn.cursor().executemany() is too slow to load largecsv files... so i use the command line instead for flights.csv
            subprocess.run(['sqlite3',
                         "example.db",
                         '-cmd',
                         '.mode csv',
                         '.import flights-small.csv Flights'])
            
        except sqlite3.Error:
            print("clear table SQL execution meets Error")


    '''
   * Implement the create user function.
   *
   * @param username   new user's username. User names are unique the system.
   * @param password   new user's password.
   * @param initAmount initial amount to deposit into the user's account, should be >= 0 (failure
   *                   otherwise).
   *
   * @return either "Created user `username`\n" or "Failed to create user\n" if failed.
    '''

    def transactionCreateCustomer(self, username, password, initAmount):
        #this is an example function.
        response = ""
        try:
            if(initAmount >= 0):
                self.conn.cursor().execute(self.CREATE_CUSTOMER_SQL.format(username.lower(), password, initAmount))
                response = "Created user {}\n".format(username)
            else:
                response = "Failed to create user\n"
        except apsw.ConstraintError:
            #we already have this customer. we can not create it again
            #print("create user meets apsw.ConstraintError")
            response = "Failed to create user\n"
        return response

    '''
   * Takes a user's username and password and attempts to log the user in.
   *
   * @param username user's username
   * @param password user's password
   *
   * @return If someone has already logged in, then return "User already logged in\n" For all other
   *         errors, return "Login failed\n". Otherwise, return "Logged in as [username]\n".
    '''

    def transactionLogin(self, username, password):
        response = ""
        try:
            if(not self.username):
                db_cursor = self.conn.cursor().execute(self.CUSTOMER_LOGIN_SQL.format(username.lower(), password))
                for row in db_cursor:
                    self.username = row[0]
                assert self.username
                response = "Logged in as {}\n".format(self.username)
            else:
                response = "User already logged in\n"
        except Exception:
            response = "Login failed\n"
        return response

    '''
   * Implement the search function.
   *
   * Searches for flights from the given origin city to the given destination city, on the given day
   * of the month. If {@code directFlight} is true, it only searches for direct flights, otherwise
   * is searches for direct flights and flights with two "hops." Only searches for up to the number
   * of itineraries given by {@code numberOfItineraries}.
   *
   * The results are sorted based on total flight time.
   *
   * @param originCity
   * @param destinationCity
   * @param directFlight        if true, then only search for direct flights, otherwise include
   *                            indirect flights as well
   * @param dayOfMonth
   * @param numberOfItineraries number of itineraries to return
   *
   * @return If no itineraries were found, return "No flights match your selection\n". If an error
   *         occurs, then return "Failed to search\n".
   *
   *         Otherwise, the sorted itineraries printed in the following format:
   *
   *         Itinerary [itinerary number]: [number of flights] flight(s), [total flight time]
   *         minutes\n [first flight in itinerary]\n ... [last flight in itinerary]\n
   *
   *         Each flight should be printed using the same format as in the {@code Flight} class.
   *         Itinerary numbers in each search should always start from 0 and increase by 1.
   *
   * @see Flight#toString()
   '''

    def transactionSearch(self, originCity, destCity, directFlight, dayOfMonth, numberOfItineraries):
        response = ""
        try:
            direct_flights = self.conn.cursor().execute(self.DIRECT_FLIGHTS_SQL.format(originCity.lower(),
                                                                                  destCity.lower(),
                                                                                  dayOfMonth,
                                                                                  numberOfItineraries))
            self.lastItineraries = []
            for row in direct_flights:
                self.lastItineraries.append(Itinerary(row[6], Flight(*row)))
            if len(self.lastItineraries) < numberOfItineraries and not directFlight:
                indirect_flights = self.conn.cursor().execute(self.INDIRECT_FLIGHTS_SQL.format(originCity.lower(),
                                                                                               destCity.lower(),
                                                                                               dayOfMonth,
                                                                                               numberOfItineraries - len(self.lastItineraries)))
                for row in indirect_flights:
                    self.lastItineraries.append(Itinerary(row[18], Flight(*row[:9]), Flight(*row[9:18])))
            self.lastItineraries.sort(key=lambda x: x.time)
            for i in range(len(self.lastItineraries)):
                response += "Itinerary {}: ".format(i)
                response += self.lastItineraries[i].toString()
            if not response:
                response = "No flights match your selection\n"
        except Exception:
            response = "Failed to search\n"
        return response

    '''
   * Implements the book itinerary function.
   *
   * @param itineraryId ID of the itinerary to book. This must be one that is returned by search in
   *                    the current session.
   *
   * @return If the user is not logged in, then return "Cannot book reservations, not logged in\n".
   *         If the user is trying to book an itinerary with an invalid ID or without having done a
   *         search, then return "No such itinerary {@code itineraryId}\n". If the user already has
   *         a reservation on the same day as the one that they are trying to book now, then return
   *         "You cannot book two flights in the same day\n". For all other errors, return "Booking
   *         failed\n".
   *
   *         And if booking succeeded, return "Booked flight(s), reservation ID: [reservationId]\n"
   *         where reservationId is a unique number in the reservation system that starts from 1 and
   *         increments by 1 each time a successful reservation is made by any user in the system.
    '''
    def transactionBook(self, itineraryId):
        response = ""
        if not self.username:
            response = "Cannot book reservations, not logged in\n"
        elif not self.lastItineraries or -1 <= itineraryId >= len(self.lastItineraries):
            response = "No such itinerary {}\n".format(itineraryId)
        else:
            try:
                itinerary = self.lastItineraries[itineraryId]
                with self.conn:
                    assert not self.checkFlightSameDay(self.username, self.lastItineraries[itineraryId].flights[0].dayOfMonth), "You cannot book two flights in the same day\n"
                    assert not self.checkFlightIsFull(itinerary.flights[0].fid), "Booking failed\n"
                    assert not (itinerary.numFlights() == 2 and self.checkFlightIsFull(itinerary.flights[1].fid)), "Booking failed\n"
                    self.conn.cursor().execute(self.CREATE_RESERVATION_SQL.format(itinerary.itineraryPrice(),
                                                                                  itinerary.flights[0].fid,
                                                                                  itinerary.flights[1].fid,
                                                                                  0, 0, self.username,
                                                                                  itinerary.flights[0].dayOfMonth))
                    self.conn.cursor().execute(self.UPDATE_RESERVATION_ID_SQL)
                self.reservations = self.fetchAllReservations(self.username)
                reservationId = 1
                for reservation in self.reservations:
                    if reservation.rid > reservationId:
                        reservationId = reservation.rid
                response = "Booked flight(s), reservation ID: {}\n".format(reservationId)
            except AssertionError as e:
                response = e.args[0]
            except Exception as e:
                response = "Booking failed\n"
        return response

    '''
   * Implements the pay function.
   *
   * @param reservationId the reservation to pay for.
   *
   * @return If no user has logged in, then return "Cannot pay, not logged in\n" If the reservation
   *         is not found / not under the logged in user's name, then return "Cannot find unpaid
   *         reservation [reservationId] under user: [username]\n" If the user does not have enough
   *         money in their account, then return "User has only [balance] in account but itinerary
   *         costs [cost]\n" For all other errors, return "Failed to pay for reservation
   *         [reservationId]\n"
   *
   *         If successful, return "Paid reservation: [reservationId] remaining balance:
   *         [balance]\n" where [balance] is the remaining balance in the user's account.
    '''
    def transactionPay(self, reservationId):
        response = ""
        if not self.username:
            response = "Cannot pay, not logged in\n"
        elif not self.checkUnpaidReservation(reservationId, self.username):
            response = "Cannot find unpaid reservation {} under user: {}\n".format(reservationId, self.username)
        else:
            try:
                price = self.conn.cursor().execute(self.GET_PRICE_SQL.format(reservationId)).fetchone()[0]
                balance = self.conn.cursor().execute(self.GET_BALANCE_SQL.format(self.username)).fetchone()[0]
                if balance < price:
                    response = "User has only {} in account but itinerary costs {}\n".format(balance, price)
                else:
                    with self.conn:
                        self.conn.cursor().execute(self.PAY_FOR_RESERVATION_SQL.format(reservationId))
                        self.conn.cursor().execute(self.UPDATE_BALANCE_SQL.format(balance - price, self.username))
                    self.reservations = self.fetchAllReservations(self.username)
                    response = "Paid reservation: {} remaining balance: {}\n".format(reservationId, balance - price)
            except Exception:
                response = "Failed to pay for reservation {}\n".format(reservationId)
        return response
                
    '''
   * Implements the reservations function.
   *
   * @return If no user has logged in, then return "Cannot view reservations, not logged in\n" If
   *         the user has no reservations, then return "No reservations found\n" For all other
   *         errors, return "Failed to retrieve reservations\n"
   *
   *         Otherwise return the reservations in the following format:
   *
   *         Reservation [reservation ID] paid: [true or false]:\n [flight 1 under the
   *         reservation]\n [flight 2 under the reservation]\n Reservation [reservation ID] paid:
   *         [true or false]:\n [flight 1 under the reservation]\n [flight 2 under the
   *         reservation]\n ...
   *
   *         Each flight should be printed using the same format as in the {@code Flight} class.
   *
   * @see Flight#toString()
    '''
    def transactionReservation(self):
        response = ""
        try:
            if not self.username:
                response = "Cannot view reservations, not logged in\n"
            else:
                self.reservations = self.fetchAllReservations(self.username)
                if len(self.reservations) < 1:
                    response = "No reservations found\n"
                else:
                    for reservation in self.reservations:
                        response += reservation.toString()
        except Exception:
            response = "Failed to retrieve reservations\n"
        return response

    '''
   * Implements the cancel operation.
   *
   * @param reservationId the reservation ID to cancel
   *
   * @return If no user has logged in, then return "Cannot cancel reservations, not logged in\n" For
   *         all other errors, return "Failed to cancel reservation [reservationId]\n"
   *
   *         If successful, return "Canceled reservation [reservationId]\n"
   *
   *         Even though a reservation has been canceled, its ID should not be reused by the system.
    '''
    def transactionCancel(self, reservationId):
        response = ""
        try:
            if not self.username:
                response = "Cannot cancel reservations, not logged in\n"
            else:
                flag = False
                for reservation in self.reservations:
                    if reservation.rid == reservationId:
                        flag = True
                assert flag, "No reservation found!"
                flag = not self.checkUnpaidReservation(reservationId, self.username)
                if flag:
                    price = self.conn.cursor().execute(self.GET_PRICE_SQL.format(reservationId)).fetchone()[0]
                    balance = self.conn.cursor().execute(self.GET_BALANCE_SQL.format(self.username)).fetchone()[0]
                with self.conn:
                    self.conn.cursor().execute(self.CANCEL_RESERVATION_SQL.format(reservationId))
                    if flag:
                        self.conn.cursor().execute(self.UPDATE_BALANCE_SQL.format(balance + price, self.username))
                self.reservations = self.fetchAllReservations(self.username)
                response = "Canceled reservation {}\n".format(reservationId)
        except Exception:
            response = "Failed to cancel reservation {}\n".format(reservationId)
        return response


    '''
    Example utility function that uses prepared statements
    '''
    def checkFlightCapacity(self, fid):
        #a helper function that you will use to implement previous functions
        result = self.conn.cursor().execute(self.CHECK_FLIGHT_CAPACITY.format(fid)).fetchone()
        if(result != None):
            return result[0]
        else:
            return 0

    def checkFlightIsFull(self, fid):
        #a helper function that you will use to implement previous functions
        
        capacity = self.conn.cursor().execute(self.CHECK_FLIGHT_CAPACITY.format(fid)).fetchone()[0]
        booked_seats = self.conn.cursor().execute(self.CHECK_BOOKED_SEATS.format(fid, fid)).fetchone()[0]
        #print("Checking booked/capacity {}/{}".format(booked_seats, capacity))
        return booked_seats >= capacity


    def checkFlightSameDay(self, username, dayOfMonth):
        result = self.conn.cursor().execute(self.CHECK_FLIGHT_DAY.format(username, dayOfMonth)).fetchall()
        if(len(result) == 0):
            #have not found there are multiple flights on the specific day by current user.
            return False
        else:
            return True

    def checkUnpaidReservation(self, rid, username):
        #a helper function that you will use to implement previous functions
        result = self.conn.cursor().execute(self.CHECK_UNPAID_RESERVATION_SQL.format(rid, username)).fetchone()
        if(result != None):
            return True
        else:
            return False

    def getBalance(self, username):
        # a helper function that you will use to implement previous functions
        balance = self.conn.cursor().execute(self.GET_BALANCE_SQL.format(username)).fetchone()[0]
        return balance

    def fetchAllReservations(self, username):
        # a helper function that you will use to implement previous functions
        cursor = self.conn.cursor().execute(self.SELECT_RESERVATION_SQL.format(username))
        reservations = []
        for row in cursor:
            flight1 = self.conn.cursor().execute(self.SELECT_FLIGHT_SQL.format(row[1])).fetchone()
            flight1 = Flight(*flight1)
            flight2 = self.conn.cursor().execute(self.SELECT_FLIGHT_SQL.format(row[2])).fetchone()
            flight2 = Flight(*flight2) if flight2 else Flight()
            reservations.append(Reservation(row[0], row[3], flight1, flight2))
        return reservations
