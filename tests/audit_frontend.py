import re
import os

def audit():
    with open('frontend/index.html', 'r', encoding='utf-8') as f:
        html_content = f.read()

    # Extract all IDs in index.html
    html_ids = set(re.findall(r'id=["\']([^"\']+)["\']', html_content))

    js_files = ['frontend/js/api.js', 'frontend/js/app.js', 'frontend/js/viewer_3d.js']
    missing = []
    found = 0
    for js_file in js_files:
        with open(js_file, 'r', encoding='utf-8') as f:
            js_content = f.read()
        js_ids = set(re.findall(r'document\.getElementById\(["\']([^"\']+)["\']\)', js_content))
        for jid in js_ids:
            if jid.startswith('floor-tab-') or jid.startswith('layer-'):
                continue
            if jid not in html_ids:
                missing.append((js_file, jid))
            else:
                found += 1

    print(f"Total HTML element IDs: {len(html_ids)}")
    print(f"Total verified JS getElementById references: {found}")
    if missing:
        print("Missing Element IDs:")
        for mf, mid in missing:
            print(f"  - {mf}: '{mid}'")
    else:
        print("[PASS] All JavaScript DOM element ID references exist in index.html!")

    # Check onclick functions in HTML exist in JS
    onclick_calls = set(re.findall(r'onclick=["\']([a-zA-Z0-9_]+)\(', html_content))
    all_js = ""
    for js_file in js_files:
        with open(js_file, 'r', encoding='utf-8') as f:
            all_js += f.read() + "\n"
    
    missing_funcs = []
    for fn in onclick_calls:
        if f"function {fn}" not in all_js and f"{fn}(" not in all_js and f"window.{fn}" not in all_js and fn not in ["openModal", "closeModal", "alert"]:
            missing_funcs.append(fn)

    print(f"Total HTML onclick handler functions: {len(onclick_calls)}")
    if missing_funcs:
        print("Missing onclick functions:")
        for mf in missing_funcs:
            print(f"  - {mf}")
    else:
        print("[PASS] All HTML onclick handlers exist and are defined in JavaScript!")

if __name__ == '__main__':
    audit()
