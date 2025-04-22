class TableFormatter:
    """
    Formats parameters + a list of rows into HTML.
    """
    def __init__(self, expr, initial_y, start, end, step):
        self.expr      = expr
        self.initial_y = initial_y
        self.start     = start
        self.end       = end
        self.step      = step

    def params_to_string(self) -> str:
        return (
            f"Expr: {self.expr} | y₀: {self.initial_y} | "
            f"x∈[{self.start}, {self.end}] Δx={self.step}"
        )

    def format_output(self, values: list) -> str:
        html = [
            '<table class="table table-striped table-bordered">',
            '<thead><tr>',
            '<th>x</th><th>Expected y</th><th>Actual y</th>',
            '<th>Abs Error</th><th>Rel Error</th>',
            '</tr></thead><tbody>'
        ]
        for r in values:
            html.append(
                f"<tr>"
                f"<td>{r['x']}</td>"
                f"<td>{r['expected']}</td>"
                f"<td>{r['actual']}</td>"
                f"<td>{r['abs_error']}</td>"
                f"<td>{r['rel_error']}</td>"
                f"</tr>"
            )
        html.append('</tbody></table>')
        return ''.join(html)