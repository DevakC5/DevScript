# devlang/charts/__init__.py — SVG chart rendering

def render_svg_chart(filename, labels, values, chart_type, title="DevLang Chart"):
    import os
    w = 600
    h = 400
    n = len(labels) if labels else 1
    bar_w = max(20, (w - 80) // n - 10)
    max_val = max(values) if values else 1
    if max_val == 0: max_val = 1
    bars = ""
    for i in range(n):
        bar_h = int((values[i] / max_val) * (h - 80))
        x = 50 + i * (bar_w + 10)
        y = h - 40 - bar_h
        color = "#" + format((i * 60) % 255, '02x') + format((i * 120) % 255, '02x') + "cc"
        bars += f'<rect x="{x}" y="{y}" width="{bar_w}" height="{bar_h}" fill="{color}" />'
        bars += f'<text x="{x + bar_w // 2}" y="{h - 20}" text-anchor="middle" font-size="10">{labels[i]}</text>'

    if chart_type == "line":
        points = " ".join(
            f"{50 + i * ((w - 80) // max(1, n - 1))},{h - 40 - int((values[i] / max_val) * (h - 80))}"
            for i in range(n)
        )
        bars = f'<polyline points="{points}" fill="none" stroke="#4682b4" stroke-width="2" />'

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}">
  <rect width="100%" height="100%" fill="white"/>
  <text x="{w // 2}" y="25" text-anchor="middle" font-size="16" font-weight="bold">{title}</text>
  <g transform="translate(0, 10)">{bars}</g>
</svg>'''
    filepath = str(filename)
    if '.' not in os.path.basename(filepath):
        filepath += '.svg'
    with open(filepath, 'w') as f:
        f.write(svg)
    return f"Saved {chart_type} chart to {filepath}"


def plot_bar(labels, values):
    return render_svg_chart("bar_chart.svg", labels, values, "bar")


def plot_line(labels, values):
    return render_svg_chart("line_chart.svg", labels, values, "line")


def plot_scatter(x, y):
    return render_svg_chart("scatter.svg", x, y, "scatter")


def plot_hist(data, bins):
    if not data:
        return "No data for histogram"
    n = int(bins) if bins else 10
    labels = list(range(n))
    values = [0] * n
    mn, mx = min(data), max(data)
    span = (mx - mn) / n if mx != mn else 1
    for d in data:
        idx = min(int((d - mn) / span), n - 1)
        values[idx] += 1
    return render_svg_chart("histogram.svg", [str(l) for l in labels], values, "bar", title="Histogram")


def plot_cartesian(x, y):
    return render_svg_chart("cartesian.svg", x, y, "scatter", title="Cartesian Plot")


def plot_3d_scatter(x, y, z):
    return "3D Scatter (not supported in SVG output)"


def plot_save(filename, labels, values, title="DevLang Chart", chart_type="bar"):
    return render_svg_chart(filename, labels, values, chart_type, title)
