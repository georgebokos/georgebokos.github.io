#!/usr/bin/env python3
"""
Build script: creates obfuscated production build in ./dist/
Run via GitHub Actions on every push to main.
"""
import os, subprocess, shutil, sys

SRC  = os.path.dirname(os.path.abspath(__file__))
DIST = os.path.join(SRC, 'dist')

OBF_FLAGS = [
    '--compact',                       'true',
    '--control-flow-flattening',       'false',   # safe — no logic changes
    '--dead-code-injection',           'false',   # safe
    '--debug-protection',              'false',   # safe
    '--disable-console-output',        'false',
    '--identifier-names-generator',    'hexadecimal',
    '--rename-globals',                'false',   # CRITICAL: onclick= handlers must keep names
    '--self-defending',                'false',   # safe
    '--simplify',                      'true',
    '--split-strings',                 'false',   # safe
    '--string-array',                  'true',
    '--string-array-encoding',         'none',
    '--string-array-threshold',        '0.6',
    '--string-array-rotate',           'true',
    '--string-array-shuffle',          'true',
    '--unicode-escape-sequence',       'false',
]

def obfuscate(src_path, dst_path):
    result = subprocess.run(
        ['javascript-obfuscator', src_path, '--output', dst_path] + OBF_FLAGS,
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f'ERROR obfuscating {src_path}:\n{result.stderr}', file=sys.stderr)
        sys.exit(1)
    print(f'  ✓ {os.path.basename(src_path)}')

def main():
    print('=== FoodDaily Build ===')

    # Clean dist
    shutil.rmtree(DIST, ignore_errors=True)
    os.makedirs(DIST)

    # --- 1. Copy static assets as-is ---
    print('\n[1/3] Copying assets...')
    # Folders to copy entirely
    COPY_DIRS = ['images', '.well-known', 'lang']
    for d in COPY_DIRS:
        src_d = os.path.join(SRC, d)
        if os.path.isdir(src_d):
            shutil.copytree(src_d, os.path.join(DIST, d))
            print(f'  ✓ {d}/ ({len(os.listdir(src_d))} files)')
    # Root files to copy.
    # ΡΗΤΗ ΛΙΣΤΑ, όχι λίστα εξαιρέσεων. Με τη λίστα εξαιρέσεων δημοσιευόταν στο
    # ζωντανό site ό,τι έμπαινε στη ρίζα — ανάμεσά τους το CLAUDE.md με εσωτερικές
    # σημειώσεις και τα logo_proposals.html. Ό,τι δεν είναι εδώ, δεν ανεβαίνει.
    PUBLISH = {'manifest.json', 'privacy.html', 'dances.html', 'icon.svg', 'install.html',
               'og-preview-el.jpg', 'og-preview-en.jpg'}
    for f in sorted(os.listdir(SRC)):
        if os.path.isdir(os.path.join(SRC, f)):
            continue
        if f not in PUBLISH and not (f.startswith('icon-') and f.endswith('.png')):
            continue
        shutil.copy2(os.path.join(SRC, f), os.path.join(DIST, f))
        print(f'  ✓ {f}')

    # --- 2. Obfuscate index.html inline JS ---
    print('\n[2/3] Obfuscating index.html...')
    with open(os.path.join(SRC, 'index.html'), 'r', encoding='utf-8') as f:
        html = f.read()

    # Locate the single <script> block
    script_open_tag = '<script>'
    script_close_tag = '</script>'
    start_tag_pos = html.index(script_open_tag)
    js_start = start_tag_pos + len(script_open_tag)
    js_end   = html.rindex(script_close_tag)

    js_src = html[js_start:js_end]

    # Write to temp, obfuscate, read back
    tmp_in  = '/tmp/fd_app_src.js'
    tmp_out = '/tmp/fd_app_obf.js'
    with open(tmp_in, 'w', encoding='utf-8') as f:
        f.write(js_src)

    obfuscate(tmp_in, tmp_out)

    with open(tmp_out, 'r', encoding='utf-8') as f:
        js_obf = f.read()

    # Re-inject obfuscated JS back into HTML
    new_html = (
        html[:start_tag_pos + len(script_open_tag)]
        + '\n' + js_obf + '\n'
        + html[js_end:]
    )
    with open(os.path.join(DIST, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(new_html)
    print(f'  ✓ index.html ({len(js_src):,} → {len(js_obf):,} chars JS)')

    # --- 3. Obfuscate service-worker.js ---
    print('\n[3/3] Obfuscating service-worker.js...')
    obfuscate(
        os.path.join(SRC, 'service-worker.js'),
        os.path.join(DIST, 'service-worker.js')
    )

    # --- Done ---
    print(f'\n✅ Build complete → dist/ ({sum(os.path.getsize(os.path.join(dp,f)) for dp,dn,fn in os.walk(DIST) for f in fn) // 1024} KB total)')

if __name__ == '__main__':
    main()
