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
    # All PNG icons at root
    for f in os.listdir(SRC):
        if f.endswith('.png') or f == 'manifest.json' or f == 'privacy.html':
            shutil.copy2(os.path.join(SRC, f), os.path.join(DIST, f))
            print(f'  ✓ {f}')
    # images/ folder
    img_src = os.path.join(SRC, 'images')
    if os.path.isdir(img_src):
        shutil.copytree(img_src, os.path.join(DIST, 'images'))
        print(f'  ✓ images/ ({len(os.listdir(img_src))} files)')

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
