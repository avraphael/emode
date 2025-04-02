import sympy as sp
import numpy as np
import matplotlib.pyplot as plt
import texttable as tt
from scipy.integrate import solve_ivp

# The program uses a LinkedList data structure in order to store the iterations of the EMODE solver. Each node
# contains the relevant information related to each interation. It is ordered in such a way that the first
# node in the list is the first iteration. This makes it easy to access data and debug.
class Node:
    def __init__(self, targetX, expectedY, actualY, absError, relError):
        self.targetX = targetX
        self.expectedY = expectedY
        self.actualY = actualY
        self.absError = absError
        self.relError = relError
        self.next = None

# We also use class objects in order to organize our LinkedList and related functions. This is preferable over
# as it makes the code much easier to read.
class EmodeList:
    # Initialize the LinkedList with no iterations.
    def __init__(self):
        self.head = None

    # The 'safeFloat()' function takes the values for each iteration and attempts to truncate them to four
    # decimal places. If this isn't possible, a string is returned which indicates that there is no applicable
    # solution.
    def safeFloat(self, value):
        try:
            return round(float(value), 4)
        except:
            return "n/a"


    # The 'insertIteration()' function inserts a new node into the LinkedList whenever there is a new interation
    # from EMODE.
    def insertIteration(self, targetX, expectedY, actualY, absError, relError):
        newNode = Node(targetX, expectedY, actualY, absError, relError)
        # If there are no existing iterations
        if self.head is None:
            self.head = newNode

        # If there are existing iterations
        else:
            tempNode = self.head
            # Traverse the LinkedList until the end is reached
            while tempNode.next is not None:
                tempNode = tempNode.next
            # Add node to the end of the LinkedList
            tempNode.next = newNode

    # The 'addToTable()' function passes a node's data to the ASCII table. We use the Texttable package in order to accomplish this.
    def addToTable(self):
        # Create new table
        table = tt.Texttable()
        # Assign columns
        table.set_cols_align(["c", "c", "c", "c", "c"])
        # Assign column names
        table.header(["Target x-values:", "Expected y-values:", "Actual y-values:", "Absolute error", "Relative error"])

        # Start from the top of the LinkedList
        tempNode = self.head
        while tempNode:
            # Add each iteration's data to the list
            table.add_row([
                self.safeFloat(tempNode.targetX),
                self.safeFloat(tempNode.expectedY),
                self.safeFloat(tempNode.actualY),
                self.safeFloat(tempNode.absError),
                self.safeFloat(tempNode.relError)
            ])
            # Traverse the LinkedList
            tempNode = tempNode.next

        # Return the table
        return table.draw()

# Welcome message for the user. It encourages them to visit the GitHub page for documentation.
print("Welcome to the EMODE (Euler's Method for Differential Equations) program!")
print("This program takes a first-order differential equation and uses numerical methods")
print("to approximate solutions to the original function.")
print("To view documentation, please visit https://github.com/avraphael/emode.")

# Assign variables using SymPy
x = sp.Symbol('x')
y = sp.Symbol('y')

# Allows the user to input required data.
stringODE = input("Please enter a first-order ordinary differential equation:\n")
initialX = float(input("Please enter the initial x coordinate: \n"))
initialY = float(input("Please enter the initial y coordinate: \n"))
stepsize = float(input("Please enter a step-size: \n"))
desiredX = float(input("What is the desired x coordinate: \n"))

# This try/except block attempts to convert the string ODE inputted by the user into
# a symbolic expression. If this fails for whichever reason, an error is thrown
# and the program will close.
try:
    sympifiedODE = sp.sympify(stringODE)
except Exception as e:
    print("Failed to parse ODE:", e)
    exit()

# This if/elif statement checks whether the ODE is in terms of x, y or both variables.
# This is needed as it changes what syntax is needed in order to solve the initial value
# problems.
if sympifiedODE.has(x, y):
    # ODE in terms of both x and y
    lambdifiedODE = sp.lambdify((x, y), sympifiedODE, modules=["numpy", "math", "sympy"])
    odeType = "xy"
elif sympifiedODE.has(x):
    # ODE in terms of x only
    lambdifiedODE = sp.lambdify(x, sympifiedODE, modules=["numpy", "math", "sympy"])
    odeType = "x"
elif sympifiedODE.has(y):
    # ODE in terms of y only
    lambdifiedODE = sp.lambdify(y, sympifiedODE, modules=["numpy", "math", "sympy"])
    odeType = "y"
else:
    print("Unrecognized ODE format.")
    exit()

# Stores the x and y values from EMODE in respective lists
xValsEuler = [initialX]
yValsEuler = [initialY]

# Initialize the LinkedList
emodeData = EmodeList()
# Set the current x and y values to be equal to the initial values.
currentX = initialX
currentY = initialY

# The slope is calculated by plugging values into the ODE.
# This is a while statement because the values being passed
# will depend on what variables are present in the ODE.
while currentX < desiredX:
    # If ODE is in terms of x and y
    if odeType == "xy":
        slope = lambdifiedODE(currentX, currentY)
    # If ODE is in terms of x alone
    elif odeType == "x":
        slope = lambdifiedODE(currentX)
    # If ODE is in terms of y alone
    elif odeType == "y":
        slope = lambdifiedODE(currentY)

    # Calculate the next values of x and y

    nextY = currentY + stepsize * slope
    nextX = currentX + stepsize


    # Add new x and y values to the respective list
    xValsEuler.append(nextX)
    yValsEuler.append(nextY)
    # Set current x and y values to be the new ones
    currentX, currentY = nextX, nextY

print("\nAttempting to find an analytical solution...")
try:
    def scipyODE(t, y):
        if odeType == "xy":
            return lambdifiedODE(t, y)
        elif odeType == "x":
            return lambdifiedODE(t)
        elif odeType == "y":
            return lambdifiedODE(y)

    sol = solve_ivp(
        scipyODE,
        (initialX, desiredX),
        [initialY],
        t_eval = np.arange(initialX, desiredX + stepsize, stepsize)
    )

    xValsScipy = sol.t
    yValsScipy = sol.y[0]
    print("SciPy solution found.")
except Exception as e:
    print("No analytical solution found.\n")
    xValsScipy = []
    yValsScipy = []

# Fill table
for xi, yi in zip(xValsEuler, yValsEuler):
    if xValsScipy is not None and len(xValsScipy) > 0:
        idx = np.where(np.isclose(xValsScipy, xi, atol=1e-5))[0]
        expectedY = yValsScipy[idx[0]] if idx.size > 0 else None
    else:
        expectedY = None

    absError = abs(expectedY - yi) if expectedY is not None else None
    relError = absError / abs(expectedY) if expectedY not in [None, 0] else None
    emodeData.insertIteration(xi, expectedY, yi, absError, relError)

# Output table
print("\nEMODE table:")
print(emodeData.addToTable())

# Plot
plt.plot(xValsEuler, yValsEuler, label="Euler's Method approximation", marker='o')
if xValsScipy is not None and len(xValsScipy) > 0:
    plt.plot(xValsScipy, yValsScipy, label="SciPy solution", linestyle='--')

plt.title("EMODE solution")
plt.xlabel("x")
plt.ylabel("y")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.savefig("EMODEplot.png")
print("\nPlot saved as 'EMODEplot.png'")
