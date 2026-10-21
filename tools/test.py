"""跑全部测试（无 pytest 依赖）。用法: python3 tools/test.py"""
import sys, traceback

import pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

import tests.test_fav_random as fav
import tests.test_full as full

CASES = [
    fav.test_characters_data,
    fav.test_npc_names_zh,
    fav.test_inject_script,
    fav.test_logo_removed,
    fav.test_versions_stamped,
    fav.test_dist_matches_live,
    full.test_manifest_complete,
    full.test_bundle_patched,
]

def main():
    failed = 0
    for fn in CASES:
        try:
            fn()
            print(f"PASS {fn.__name__}")
        except Exception:
            failed += 1
            print(f"FAIL {fn.__name__}")
            traceback.print_exc(limit=2)
    print(f"{len(CASES) - failed}/{len(CASES)} passed")
    return 1 if failed else 0

if __name__ == "__main__":
    sys.exit(main())
