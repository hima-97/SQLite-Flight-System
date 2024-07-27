import unittest
import os
import Query
import FlightService
import concurrent.futures
from concurrent.futures import ProcessPoolExecutor
from concurrent.futures import ThreadPoolExecutor
import time
from multiprocessing import Process
import apsw

# User class to store commands and expected results for each user
class User:
    def __init__(self, cmds, results):
        # Initialize with commands and expected results
        self.cmds = cmds
        self.results = results

    # Executes all commands for the user and returns the combined output
    def call(self):
        self.q = Query.Query()
        outputBuffer = ""
        for cmd in self.cmds:
            # Execute each command and append the result to outputBuffer
            outputBuffer += FlightService.execute(self.q, cmd)      
        return outputBuffer
    
    # Debug method to print commands and results
    def toString(self):
        print("cmds:", self.cmds)
        print("results:", self.results)

# Constants for parsing test case files
COMMENTS = "#"
DELIMITER = "*"
SEPARATOR = "|"

# Parses a test case file and returns a list of User objects
def parse_testcase(testcase_filename):
    users = []
    cmds = []
    results = []
    output_buffer = ""
    with open(testcase_filename, 'r') as f:
        lines = f.readlines()
        isCMD = True  # Flag to distinguish between commands and results
        for line in lines:
            if line[0] == COMMENTS:  # Ignore comments
                continue
            elif line[0] == DELIMITER:
                if isCMD:
                    isCMD = False  # Switch to reading results
                else:
                    # End of current user's possible results
                    results.append(output_buffer)
                    users.append(User(cmds, results))
                    cmds = []
                    results = []
                    output_buffer = ""
                    isCMD = True  # Switch back to reading commands
            elif line[0] == SEPARATOR:
                if isCMD:
                    raise Exception("wrong testcase format!")
                else:
                    # Separate multiple possible results for the same user
                    results.append(output_buffer)
                    output_buffer = ""
            else:
                # Remove inline comments and split between commands and results
                line_without_comments = line.split("#", 2)[0]
                if isCMD:
                    cmds.append(line_without_comments)
                else:
                    output_buffer += line_without_comments
    return users  # Return the list of User objects

# Test class for the flight service
class TestFlightService(unittest.TestCase):

    # Test method for non-concurrent test cases
    def test_non_concurrency(self):
        non_concurrent_testcases = os.listdir("testcases/non_concurrent/")
        counter = 0  # Track the number of test cases
        score = 0  # Track the number of passed test cases
        for testcase in non_concurrent_testcases:
            q = Query.Query()
            q.clearTables()  # Clear the database before each test case
            users = parse_testcase(os.path.join("testcases/non_concurrent/", testcase))
            counter += 1
            passed = True
            for user in users:
                output = user.call()
                # Compare the output with the expected result
                if output != user.results[0]:
                    passed = False
                    print("testcase {} fails, score for non_concurrent test {}/{}".format(testcase, score, counter))
                    print("your output for testcase {} is:\n {}".format(testcase, output))
            if passed:
                score += 1
                print("testcase {} passes, score for non_concurrent test {}/{}".format(testcase, score, counter))

    # Test method for concurrent test cases
    def test_concurrency(self):
        concurrent_testcases = os.listdir("testcases/concurrent/")
        counter = 0  # Track the number of test cases
        score = 0  # Track the number of passed test cases
        for testcase in concurrent_testcases:
            users = parse_testcase(os.path.join("testcases/concurrent/", testcase))
            with ProcessPoolExecutor(max_workers=3) as executor:
                # Multiple tests for each concurrent test case
                for i in range(5):
                    time.sleep(1)  # Wait for a short period before each test
                    counter += 1
                    q = Query.Query()
                    q.clearTables()  # Clear the database before each test case
                    futures = []
                    for user in users:
                        # Execute user commands concurrently
                        futures.append(executor.submit(user.call))
                    passed = False
                    for k in range(len(users[0].results)):
                        # Only need to pass one of the possible outputs. Concurrent execution is non-deterministic
                        if (futures[0].result().strip() == users[0].results[k].strip() and
                                futures[1].result().strip() == users[1].results[k].strip()):
                            passed = True
                    if passed:
                        score += 1
                        print("testcase {} passes, score for concurrent tests so far: {}/{}".format(testcase, score, counter))
                    else:
                        print("testcase {} fails, score for concurrent tests so far: {}/{}".format(testcase, score, counter))
                        print("your output for testcase {}\n\n user1 :\n {}\n\n user2 :\n {}\n\n".format(testcase, futures[0].result().strip(), futures[1].result().strip()))

# Run the test cases when the script is executed
if __name__ == '__main__':
    unittest.main()
