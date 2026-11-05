"""Bundle hash-verified, pinned query weights during packaging, never at request time."""

import hashlib
import json
from pathlib import Path
from tempfile import NamedTemporaryFile
from urllib.request import Request, urlopen


def prepare(directory: Path) -> None:
    artifact = json.loads((directory / 'artifact.json').read_text(encoding='utf-8'))
    unsigned = {key: value for key, value in artifact.items() if key != 'version'}
    checksum = hashlib.sha256(json.dumps(unsigned, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    if (artifact.get('version') != 'm2-' + checksum[:24]
            or artifact.get('model_id') != 'sentence-transformers/all-MiniLM-L6-v2'
            or artifact.get('model_revision') != '1110a243fdf4706b3f48f1d95db1a4f5529b4d41'
            or artifact.get('dimensions') != 384):
        raise ValueError('Invalid bundled catalog/model manifest')
    for filename, source, key, limit in (
        ('tokenizer.json', 'tokenizer.json', 'tokenizer_sha256', 2 * 1024 * 1024),
        ('model.onnx', 'onnx/model.onnx', 'model_sha256', 100 * 1024 * 1024),
    ):
        destination = directory / filename
        if destination.is_file():
            with destination.open('rb') as stream:
                if hashlib.file_digest(stream, 'sha256').hexdigest() == artifact[key]:
                    continue
            raise ValueError(f'Cached semantic asset checksum mismatch: {filename}')
        url = f"https://huggingface.co/{artifact['model_id']}/resolve/{artifact['model_revision']}/{source}"
        temporary = None
        try:
            with urlopen(Request(url, headers={'User-Agent': 'Current-semantic-build/1.0'}), timeout=120) as response:
                with NamedTemporaryFile(dir=directory, delete=False) as output:
                    temporary = Path(output.name)
                    sha, size = hashlib.sha256(), 0
                    while chunk := response.read(1024 * 1024):
                        size += len(chunk)
                        if size > limit:
                            raise ValueError(f'Semantic asset exceeds size bound: {filename}')
                        output.write(chunk)
                        sha.update(chunk)
            if sha.hexdigest() != artifact[key]:
                raise ValueError(f'Downloaded semantic asset checksum mismatch: {filename}')
            temporary.replace(destination)
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)


if __name__ == '__main__':
    prepare(Path(__file__).parent / 'src/game_discovery/assets')
