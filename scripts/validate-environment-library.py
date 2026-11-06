"""Check portable-library references, hashes, GLB resources and archive contents.

This is a bounded consumer check, not a replacement for Khronos conformance
validation or visual review in another engine. Uses only the Python standard library.
"""
from pathlib import Path
import hashlib
import json
import struct
import zipfile

ROOT=Path(__file__).resolve().parents[1]
LIBRARY=ROOT/'asset-library'


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def references(value,folder):
    if isinstance(value,dict):
        if isinstance(value.get('file'),str):
            path=(folder/value['file']).resolve()
            assert path.is_relative_to(LIBRARY.resolve()) and path.is_file(),path
            if 'sha256' in value:assert sha(path).lower()==value['sha256'].lower(),path
        if isinstance(value.get('licenseFile'),str):
            path=(folder/value['licenseFile']).resolve()
            assert path.is_relative_to(LIBRARY.resolve()) and path.is_file(),path
        for child in value.values():references(child,folder)
    elif isinstance(value,list):
        for child in value:references(child,folder)


def glb(path):
    data=path.read_bytes();magic,version,size=struct.unpack_from('<4sII',data)
    assert magic==b'glTF' and version==2 and size==len(data),path
    count,kind=struct.unpack_from('<I4s',data,12);assert kind==b'JSON'
    doc=json.loads(data[20:20+count]);assert doc['asset']['version']=='2.0'
    assert not doc.get('extensionsRequired'),path
    assert len(doc.get('buffers',[]))==1 and 'uri' not in doc['buffers'][0],path
    start=20+count;binarySize,binaryType=struct.unpack_from('<I4s',data,start)
    assert binaryType==b'BIN\x00' and start+8+binarySize==len(data),path
    blob=data[start+8:]
    for view in doc.get('bufferViews',[]):
        assert view.get('byteOffset',0)+view['byteLength']<=binarySize,path
    images=[]
    for image in doc.get('images',[]):
        assert 'uri' not in image and image['mimeType']=='image/png',path
        view=doc['bufferViews'][image['bufferView']];offset=view.get('byteOffset',0)
        png=blob[offset:offset+view['byteLength']]
        assert png[:8]==b'\x89PNG\r\n\x1a\n',path
        width,height=struct.unpack_from('>II',png,16)
        assert 0<width<=1024 and 0<height<=1024 and png[24]==8,path
        images.append([width,height])
    triangles=0
    for mesh in doc['meshes']:
        for primitive in mesh['primitives']:
            assert primitive.get('mode',4)==4 and 'POSITION' in primitive['attributes'],path
            accessor=doc['accessors'][primitive.get('indices',primitive['attributes']['POSITION'])]
            assert accessor['count']%3==0,path
            triangles+=accessor['count']//3
    return dict(file=path.relative_to(LIBRARY).as_posix(),sha256=sha(path),triangles=triangles,embeddedImages=images)


def main():
    manifests=list(LIBRARY.rglob('*.json'))
    for path in manifests:references(json.loads(path.read_text()),path.parent)
    models=[glb(path) for path in sorted(LIBRARY.rglob('*.glb'))]
    archive=ROOT/'build/fidelity-v1/Cinder-Environment-Assets.zip'
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        expected={f'cinder-environment/{p.relative_to(LIBRARY).as_posix()}':p for p in LIBRARY.rglob('*') if p.is_file()}
        assert set(z.namelist())==set(expected)
        for name,path in expected.items():assert hashlib.sha256(z.read(name)).hexdigest()==sha(path)
        assert not any(name.endswith(('.wav','.exe','.hpp')) for name in z.namelist())
    result=dict(scope='Portable source/manifest/archive integrity and embedded GLB texture budget; not visual or full glTF conformance.',
        passed=True,manifests=len(manifests),models=models,archiveSha256=sha(archive),files=len(expected))
    target=ROOT/'build/fidelity-v1/asset-library-check.json';target.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='models'},indent=2))


if __name__=='__main__':main()
