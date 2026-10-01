"""Repeat the synthetic MVP over HTTP. --model uses the API's configured provider.

No environment file is read by this script. Start a single API worker first.
"""
import argparse
from io import BytesIO
import json
from pathlib import Path
import time
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from uuid import uuid4
from zipfile import ZipFile
import xml.etree.ElementTree as ET


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--api', default='http://127.0.0.1:8000')
    parser.add_argument('--model', action='store_true')
    parser.add_argument('--output', type=Path, default=Path('/tmp/slidecraft-smoke.pptx'))
    args = parser.parse_args()
    def request(path, method='GET', value=None, raw=None, content_type=None):
        data = raw if raw is not None else json.dumps(value).encode() if value is not None else None
        headers = {'Content-Type': content_type or 'application/json'} if data else {}
        with urlopen(Request(args.api.rstrip('/') + path, data=data, headers=headers, method=method), timeout=120) as response:
            result = response.read()
            return json.loads(result) if 'application/json' in response.headers.get('Content-Type', '') else result

    material = request('/projects/demo/materials')
    pdf = request('/projects/demo/source.pdf')
    boundary = 'slidecraft-' + uuid4().hex
    multipart = (f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="synthetic-smoke.pdf"\r\nContent-Type: application/pdf\r\n\r\n'.encode()
                 + pdf + f'\r\n--{boundary}--\r\n'.encode())
    document = request('/documents/upload', 'POST', raw=multipart, content_type=f'multipart/form-data; boundary={boundary}')
    state = request('/projects', 'POST', dict(assignment_text=material['assignment_text'], context_pack_text=material['context_pack_text'],
                    source_document_id=document['document_id'], theme='dark_tech_pitch', language='en'))
    base = '/projects/' + state['id']
    mode = 'model' if args.model else 'template'
    state = request(base + '/outline/generate', 'POST', dict(expected_revision=state['revision'], mode=mode))
    candidates = request(base + '/source-candidates')
    assert {ref['page_number'] for ref in candidates} == {1, 2}
    outline = state['outline']
    for index, item in enumerate(outline):
        page = 2 if index in (1, 3) else 1
        item['evidence_refs'] = [next(ref for ref in candidates if ref['page_number'] == page)]
    outline[0]['title'] = 'Reviewed synthetic campus case'
    outline[1], outline[2] = outline[2], outline[1]
    for index, item in enumerate(outline, 1): item['order'] = index
    state = request(base + '/outline', 'PUT', dict(expected_revision=state['revision'], outline=outline))
    state = request(base + '/outline/approve', 'POST', dict(expected_revision=state['revision'], theme=state['theme']))
    state = request(base + '/build', 'POST', dict(expected_revision=state['revision'], mode=mode))
    snapshots = []
    edited_during_build = False
    accepted_body = 'This synthetic campus case needs human review. The results are promising, not proven.'
    deadline = time.monotonic() + 180
    previous = None
    while time.monotonic() < deadline:
        state = request(base)
        statuses = [slide['status'] for slide in state['slides']]
        if statuses != previous:
            snapshots.append(statuses)
            print('Slides:', statuses, flush=True)
            previous = statuses
        if not edited_during_build and statuses[0] == 'ready' and any(value in ('queued', 'generating') for value in statuses[1:]):
            try:
                state = request(base + '/slides/s1/blocks/body', 'PATCH', dict(expected_revision=state['revision'], text=accepted_body))
                edited_during_build = True
            except HTTPError as exc:
                if exc.code != 409: raise
        if state['phase'] in ('ready', 'error'): break
        time.sleep(0.15)
    assert state['phase'] == 'ready', 'Deck did not finish successfully'
    assert edited_during_build, 'Did not observe and edit a ready slide while later slides were pending'
    assert state['slides'][0]['blocks']['body']['text'] == accepted_body
    before = json.loads(json.dumps(state))
    if args.model:
        state = request(base + '/slides/s1/blocks/title/regenerate', 'POST', dict(expected_revision=state['revision']))
        assert state['slides'][0]['blocks']['title']['status'] == 'generating'
        deadline = time.monotonic() + 90
        while time.monotonic() < deadline:
            state = request(base)
            if state['slides'][0]['blocks']['title']['status'] != 'generating': break
            time.sleep(0.2)
        assert state['slides'][0]['blocks']['title']['status'] == 'ready'
        assert state['slides'][0]['blocks']['body'] == before['slides'][0]['blocks']['body']
        assert state['slides'][1:] == before['slides'][1:]
    deck = request(base + '/export.pptx')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(deck)
    namespace = {'a': 'http://schemas.openxmlformats.org/drawingml/2006/main'}
    with ZipFile(BytesIO(deck)) as archive:
        slides = sorted(name for name in archive.namelist() if name.startswith('ppt/slides/slide') and name.endswith('.xml'))
        assert len(slides) == 5
        for index, name in enumerate(slides):
            texts = [node.text or '' for node in ET.fromstring(archive.read(name)).findall('.//a:t', namespace)]
            saved = state['slides'][index]['blocks']
            assert saved['title']['text'] in texts
            assert saved['source_label']['text'] in texts
            for part in saved['body']['text'].split('|'):
                assert ' '.join(part.split()) in ' '.join(' '.join(texts).split())
    receipt = dict(project_id=state['id'], mode=mode, slide_count=5, edited_during_build=edited_during_build,
                   title_regeneration=args.model, snapshots=snapshots, output=str(args.output))
    args.output.with_suffix('.json').write_text(json.dumps(receipt, indent=2))
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    main()
