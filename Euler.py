from sympy import *

x,y=symbols('x y')
expr = parse_expr(input("Enter an explicit expression for a function f'(x): "))
h, x0, fx0 = map(float, input("Enter step size, x0, and f(x0): ").replace(' ','').split(","))
print(f'Your derivative: {expr}')
print(f'Analytical solution: f(x)= {integrate(expr, x)} + C')
print(f'Approximate solutions up to f({x0+h*10}):')
print('n    x_n     y_n')



for i in range(11):
    n = i 
    if n == 0:
        x_n = x0
        y_n = fx0
    else:
        x_n = x0 + n*h
        y_n = y_n + h * expr.subs(x, x_n - h)
    print(f'{n}    {round(x_n,3)}    {round(y_n,3)}')

