#!/usr/bin/env python3
"""Fail on new lint errors while retaining existing unrelated errors in reports."""
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

def errors(root):
    found = {}
    for module in ('shared', 'common', 'mobile'):
        report = root / module / 'build/reports/lint-results-debug.xml'
        if not report.is_file():
            raise RuntimeError(f'Missing lint report: {report}')
        for issue in ET.parse(report).getroot().findall('issue'):
            if issue.get('severity') not in ('Error', 'Fatal'):
                continue
            location = issue.find('location')
            file = Path(location.get('file')).resolve()
            relative = str(file.relative_to(root.resolve()))
            # Match the actual offending source, not shifting line numbers or
            # duplicate translated-resource locations of the same issue.
            source = issue.get('errorLine1', '').strip()
            if not source:
                lines = file.read_text().splitlines()
                source = lines[int(location.get('line', '1')) - 1].strip()
            key = (module, issue.get('id'), relative, source)
            found[key] = issue.get('message')
    return found

if __name__ == '__main__':
    old, new = map(errors, map(Path, sys.argv[1:3]))
    introduced = new.keys() - old.keys()
    print(f'Baseline: {len(old)} distinct existing lint errors; candidate: {len(new)}; introduced: {len(introduced)}')
    for key in sorted(introduced):
        print('NEW:', *key, new[key], sep=' | ')
    print('Existing issues remain in the unfiltered baseline and candidate XML/HTML reports.')
    sys.exit(bool(introduced))
