from flask import Flask, request, jsonify, render_template
import json
import os

app = Flask(__name__)

PROJECTS_FILE = os.path.join(os.path.dirname(__file__), 'projects.json')

def load_projects():
    with open(PROJECTS_FILE) as f:
        return json.load(f)

@app.route('/')
def index():
    projects = load_projects()
    # Collect all unique supplies for the checklist
    all_supplies = set()
    for p in projects:
        for s in p['supplies_needed']:
            all_supplies.add(s)
    return render_template('index.html', supplies=sorted(all_supplies))

@app.route('/match', methods=['POST'])
def match():
    data = request.get_json()
    owned = set(s.strip().lower() for s in data.get('owned', []))
    if len(owned) < 2:
        return jsonify({'error': 'Select at least 2 supplies to find matching projects.'}), 400

    projects = load_projects()
    results = []
    for p in projects:
        needed = set(s.lower() for s in p['supplies_needed'])
        match_count = len(owned & needed)
        if match_count == 0:
            continue
        ratio = match_count / len(needed)
        missing = needed - owned
        results.append({
            'name': p['name'],
            'category': p['category'],
            'difficulty': p['difficulty'],
            'time_estimate': p['time_estimate'],
            'tutorial_url': p['tutorial_url'],
            'description': p['description'],
            'owned_supplies': sorted(owned & needed),
            'missing_supplies': sorted(missing),
            'total_needed': len(needed),
            'match_ratio': ratio,
            'match_pct': round(ratio * 100)
        })

    results.sort(key=lambda r: (-r['match_ratio'], -r['total_needed']))
    return jsonify(results[:8])

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5198)
