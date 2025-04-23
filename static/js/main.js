export default class TableFormatter {
  constructor(expr, initialY, start, end, step) {
    this.expr     = expr;
    this.initialY = initialY;
    this.start    = start;
    this.end      = end;
    this.step     = step;
  }

  paramsToString() {
    return `Expr: ${this.expr} | y₀: ${this.initialY} | x∈[${this.start},${this.end}] Δx=${this.step}`;
  }

  formatOutput(values) {
    let html = `
      <table class="table table-striped table-bordered">
        <thead><tr>
          <th>x</th><th>Expected y</th><th>Actual y</th>
          <th>Abs Error</th><th>Rel Error</th>
        </tr></thead>
        <tbody>`;

    values.forEach(r => {
      html += `
        <tr>
          <td>${r.x}</td>
          <td>${r.expected}</td>
          <td>${r.actual}</td>
          <td>${r.abs_error}</td>
          <td>${r.rel_error}</td>
        </tr>`;
    });

    html += '</tbody></table>';
    return html;
  }
}


window.addEventListener('DOMContentLoaded', () => {
  const MQ      = MathQuill.getInterface(2);
  const inputEl = document.getElementById('math-input');
  inputEl.innerHTML = '';
  const mathField = MQ.MathField(inputEl, { spaceBehavesLikeTab: true });
  inputEl.addEventListener('mousedown', e => {
    e.preventDefault();
    mathField.focus();
  });

  // Toolbar buttons
  document.querySelectorAll('#toolbar button').forEach(btn => {
    btn.addEventListener('click', () => {
      mathField.focus();
      const { cmd, write, fraction, custom, latex } = btn.dataset;

      if (custom === 'exp') {
        // eʸ → e^{…}
        mathField.write('e^{}');
        // move cursor into the braces
        mathField.keystroke('Left');
        mathField.keystroke('Left');
      }
      else if (cmd) {
        mathField.cmd(cmd);
      }
      else if (write) {
        mathField.typedText(write === '^' ? '^' : write);
      }
      else if (latex) {
        mathField.write(latex);
      }
      else if (fraction) {
        mathField.cmd('frac');
      }
      else if (custom === 'derivative') {
        mathField.write('\\frac{dy}{dx}');
      }
      else if (custom === 'integral') {
        mathField.write('\\int () \\, dx');
        mathField.keystroke('Left');
        mathField.keystroke('Left');
      }
      else if (custom === 'definite') {
        mathField.write('\\int_{ }^{ }() \\, dx');
        mathField.keystroke('Up');
      }
      else if (custom === 'ln') {
        mathField.write('\\ln');
      }
    });
  });

  // Generate table
  document.getElementById('generate').addEventListener('click', async () => {
    let latex = mathField.latex().trim();
    if (!latex) return alert('Please enter an expression');

    // turn e^{something} into \exp(something)
    const processedLatex = latex.replace(
      /e\^\{([^}]*)\}/g,
      '\\exp($1)'
    ).replace(
      /e\^([a-zA-Z0-9])/g,
      '\\exp($1)'
      );

    console.log(latex)
    console.log(processedLatex)

    const start    = parseFloat(document.getElementById('start').value);
    const end      = parseFloat(document.getElementById('end').value);
    const step     = parseFloat(document.getElementById('step').value);
    const initialY = parseFloat(document.getElementById('initial_y').value);

    if (step <= 0) return alert('Step must be > 0');
    if (end <= start) return alert('End must be > start');

    try {
      const res = await fetch('/evaluate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          latex:      processedLatex,
          start,
          end,
          step,
          initial_y: initialY
        })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Evaluation failed');

      document.getElementById('params').textContent = data.params;
      document.getElementById('result').innerHTML  = data.table;
    } catch (err) {
      alert('Error: ' + err.message);
    }
  });
});
