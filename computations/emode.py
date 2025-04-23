import re
import numpy as np
import sympy as sp
from sympy import Eq, Derivative, E
from sympy.parsing.latex import parse_latex
from scipy.integrate import solve_ivp
import matplotlib.pyplot as plt

class EmodeList:
    """
    The program uses a LinkedList data structure in order to store the iterations of the EMODE solver.
    Each node contains the relevant information related to each iteration. It is ordered such that the
    first node in the list is the first iteration, making data access and debugging straightforward.
    """
    class Node:
        def __init__(self, x, expected, actual, abs_error, rel_error):
            """
            Node for storing a single iteration's data.
            x: target x-value
            expected: expected y-value (from analytic solution)
            actual: computed y-value (Euler)
            abs_error: absolute error
            rel_error: relative error
            """
            self.x         = x
            self.expected  = expected
            self.actual    = actual
            self.abs_error = abs_error
            self.rel_error = rel_error
            self.next      = None

    def __init__(self):
        """Initialize the LinkedList with no iterations."""
        self.head = None

    def safe_float(self, value):
        """
        Attempts to round the value to six decimal places.
        Returns 'DNE' if conversion to float fails or value is None.
        """
        try:
            if value is None:
                return 'DNE'
            return round(float(value), 6)
        except Exception:
            return 'DNE'

    def insert_iteration(self, x, expected, actual, abs_error, rel_error):
        """
        Inserts a new node into the LinkedList for each EMODE iteration.
        If no existing iterations, sets as head; otherwise, appends to the end.
        """
        new_node = EmodeList.Node(x, expected, actual, abs_error, rel_error)
        if not self.head:
            self.head = new_node
        else:
            curr = self.head
            while curr.next:
                curr = curr.next
            curr.next = new_node

    def to_dict(self):
        """
        Converts the LinkedList to a list of dictionaries for easy consumption.
        Each dictionary has keys: 'x', 'expected', 'actual', 'abs_error', 'rel_error'.
        """
        out, curr = [], self.head
        while curr:
            out.append({
                'x':         self.safe_float(curr.x),
                'expected':  curr.expected if curr.expected == 'DNE' else self.safe_float(curr.expected),
                'actual':    curr.actual if curr.actual == 'DNE' else self.safe_float(curr.actual),
                'abs_error': curr.abs_error if curr.abs_error == 'N/A' else self.safe_float(curr.abs_error),
                'rel_error': curr.rel_error if curr.rel_error == 'N/A' else self.safe_float(curr.rel_error),
            })
            curr = curr.next
        return out


class Emode:
    """
    EMODE (Euler's Method for Differential Equations) solver.
    Parses a LaTeX or sympy string for the ODE, performs Euler's method,
    computes the analytic solution via SciPy where possible, and computes errors.
    Can also plot the results.
    """
    def __init__(self, latex, initial_x, initial_y, step_size, desired_x):
        """
        Parameters:
            latex: string, first-order ODE in LaTeX or sympy-readable format
            initial_x: initial x coordinate
            initial_y: initial y coordinate
            step_size: step size for Euler's method
            desired_x: x coordinate at which to stop
        """
        self.latex           = latex
        self.initial_x       = float(initial_x)
        self.initial_y       = float(initial_y)
        self.step_size       = float(step_size)
        self.desired_x       = float(desired_x)
        self.lambdified_ode  = None
        self.ode_type        = None
        self.x_vals_euler    = []
        self.y_vals_euler    = []
        self.x_vals_analytic = []
        self.y_vals_analytic = []

    def parse_ode(self):
        """
        Parses the input LaTeX or sympy string into a sympy expression.
        Attempts real LaTeX parse, then falls back to simple sympify.
        Determines ODE type: 'xy', 'x', 'y', or 'const' and lambdifies accordingly.
        """
        try:
            raw = parse_latex(self.latex)
        except Exception:
            expr = self.latex.split('=')[1] if '=' in self.latex else self.latex
            expr = expr.replace('\\', '').replace('{', '').replace('}', '')
            expr = re.sub(r'(\d)([a-zA-Z])', r'\1*\2', expr)
            raw = sp.sympify(expr)

        # Strip Eq with Derivative if present
        if isinstance(raw, Eq):
            lhs, rhs = raw.lhs, raw.rhs
            if isinstance(lhs, Derivative):
                ode_expr = rhs
            elif isinstance(rhs, Derivative):
                ode_expr = lhs
            else:
                raise ValueError("Expected dy/dx on one side")
        else:
            ode_expr = raw

        # Handle lone 'e' symbol as Euler's number
        if isinstance(ode_expr, sp.Symbol) and ode_expr.name == 'e':
            ode_expr = E

        # Determine variables
        x, y = sp.symbols('x y')
        if ode_expr.has(x, y):
            self.lambdified_ode = sp.lambdify((x, y), ode_expr, modules=['numpy'])
            self.ode_type = 'xy'
        elif ode_expr.has(x):
            self.lambdified_ode = sp.lambdify(x, ode_expr, modules=['numpy'])
            self.ode_type = 'x'
        elif ode_expr.has(y):
            self.lambdified_ode = sp.lambdify(y, ode_expr, modules=['numpy'])
            self.ode_type = 'y'
        else:
            # Constant ODE
            c = float(ode_expr)
            self.lambdified_ode = lambda *_: c
            self.ode_type = 'const'

    def euler(self):
        """
        Executes Euler's method to approximate the solution.
        Also computes the analytic solution and errors.
        Returns:
            List of iteration data as dicts with x, expected, actual, abs_error, rel_error.
        """
        self.parse_ode()
        x_curr, y_curr = self.initial_x, self.initial_y
        self.x_vals_euler = [x_curr]
        self.y_vals_euler = [y_curr]
        emode_list = EmodeList()
        emode_list.insert_iteration(x_curr, None, y_curr, None, None)

        # Euler forward sweep
        n_steps = int(np.ceil((self.desired_x - self.initial_x) / self.step_size))
        for _ in range(n_steps):
            try:
                if self.ode_type == 'xy':
                    slope = self.lambdified_ode(x_curr, y_curr)
                elif self.ode_type == 'x':
                    slope = self.lambdified_ode(x_curr)
                elif self.ode_type == 'y':
                    slope = self.lambdified_ode(y_curr)
                else:
                    slope = self.lambdified_ode()

                # Check for invalid values
                if not np.isfinite(slope):
                    raise ValueError("Invalid slope value")

                x_next = x_curr + self.step_size
                y_next = y_curr + self.step_size * slope
                self.x_vals_euler.append(x_next)
                self.y_vals_euler.append(y_next)
                emode_list.insert_iteration(x_next, None, y_next, None, None)
                x_curr, y_curr = x_next, y_next
            except (ValueError, ZeroDivisionError, TypeError) as e:
                # If we encounter an error, mark the values as DNE
                x_next = x_curr + self.step_size
                emode_list.insert_iteration(x_next, 'DNE', 'DNE', 'N/A', 'N/A')
                x_curr = x_next
                continue

        # Analytic solve at evenly spaced points
        try:
            self._compute_analytic(n_steps + 1)
        except Exception:
            # If analytic solution fails, we'll just use DNE for expected values
            self.x_vals_analytic = []
            self.y_vals_analytic = []

        # Populate expected values and errors
        curr = emode_list.head
        while curr:
            if self.x_vals_analytic:
                try:
                    idx = min(range(len(self.x_vals_analytic)),
                              key=lambda i: abs(self.x_vals_analytic[i] - curr.x))
                    y_expected = self.y_vals_analytic[idx]
                except Exception:
                    y_expected = 'DNE'
            else:
                y_expected = 'DNE'

            if curr.actual != 'DNE' and y_expected != 'DNE':
                try:
                    abs_err = abs(float(y_expected) - float(curr.actual))
                    rel_err = abs_err / float(y_expected) if float(y_expected) != 0 else 'N/A'
                except Exception:
                    abs_err = 'N/A'
                    rel_err = 'N/A'
            else:
                abs_err = 'N/A'
                rel_err = 'N/A'

            curr.expected  = y_expected
            curr.abs_error = abs_err
            curr.rel_error = rel_err
            curr = curr.next

        return emode_list.to_dict()

    def _compute_analytic(self, n_points):
        """
        Uses SciPy's solve_ivp to compute the analytic solution (if possible)
        at n_points between initial_x and desired_x.
        """
        def ode_fn(t, y):
            if self.ode_type == 'xy':
                return self.lambdified_ode(t, y[0])
            elif self.ode_type == 'x':
                return self.lambdified_ode(t)
            elif self.ode_type == 'y':
                return self.lambdified_ode(y[0])
            else:
                return self.lambdified_ode()

        t_eval = np.linspace(self.initial_x, self.desired_x, n_points)
        sol = solve_ivp(ode_fn,
                        (self.initial_x, self.desired_x),
                        [self.initial_y],
                        t_eval=t_eval)

        self.x_vals_analytic = sol.t.tolist()
        self.y_vals_analytic = sol.y[0].tolist()

    def plot(self, filename="EMODEplot.png"):
        """
        Plots the EMODE solution including Euler's approximation and analytic solution.
        Saves the figure to the given filename.
        """
        plt.figure()
        plt.plot(self.x_vals_euler, self.y_vals_euler, label="Euler's Method approximation", marker='o')
        if self.x_vals_analytic:
            plt.plot(self.x_vals_analytic, self.y_vals_analytic, label="SciPy (analytic) solution", linestyle='--')
        plt.title("EMODE solution")
        plt.xlabel("x")
        plt.ylabel("y")
        plt.legend()
        plt.grid(True)
        plt.tight_layout()
        plt.savefig(filename)
