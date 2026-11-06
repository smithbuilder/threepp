"""Package renderer-independent source assets with a small portable catalog.

No network calls or image conversion. The game adapter lives in showcase/;
this library contains ordinary HDR/JPEG/glTF assets and their provenance.
"""
from pathlib import Path
import hashlib
import json
import shutil
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'showcase/assets'
LIBRARY = ROOT / 'asset-library'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    LIBRARY.mkdir(parents=True,exist_ok=True)
    shutil.copy2(ROOT/'LICENSE',LIBRARY/'LICENSE')
    items = []
    sets = [
        ('forest-floor', 'forest_ground_04', 3.2, 'forest',
         'https://polyhaven.com/a/forest_ground_04'),
        ('gravel-road', 'gravel_road', 2.0, 'gravel',
         'https://polyhaven.com/a/gravel_road'),
    ]
    for name, source, metres, rough, url in sets:
        folder = LIBRARY / 'materials' / name
        folder.mkdir(parents=True, exist_ok=True)
        textures = {}
        for semantic, filename, destination, space in [
            ('baseColor', f'{source}_diff_1k.jpg', 'basecolor_1k.jpg', 'sRGB'),
            ('normal', f'{source}_nor_gl_1k.jpg', 'normal_gl_1k.jpg', 'linear'),
            ('roughness', f'ground-v2-{rough}-rough-1k.jpg', 'roughness_1k.jpg', 'linear'),
        ]:
            shutil.copy2(SOURCE / filename, folder / destination)
            textures[semantic] = dict(file=destination, colorSpace=space,
                                     sha256=sha(folder / destination))
        material = dict(schemaVersion=1, id=f'material.{name}',
            model='metallic-roughness', tileSizeMetres=[metres, metres],
            metalness=0, normalConvention='OpenGL +Y tangent space',
            roughnessChannel='green (grayscale replicated in RGB)',
            textures=textures, source=url, license='CC0-1.0',
            licenseUrl='https://polyhaven.com/license')
        (folder / 'material.json').write_text(json.dumps(material, indent=2)+'\n')
        items.append(dict(id=material['id'], type='pbr-material',
                          manifest=f'materials/{name}/material.json'))
    folder = LIBRARY / 'environments/kloofendal-partly-cloudy'
    folder.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SOURCE / 'sky-lighting-kloofendal-1k.hdr', folder / 'sky_1k.hdr')
    source = json.loads((SOURCE / 'sky-lighting-kloofendal-SOURCE.json').read_text())
    sky = dict(schemaVersion=1, id='environment.kloofendal-partly-cloudy',
        file='sky_1k.hdr', projection='equirectangular', dimensions=[1024,512],
        colorSpace='linear HDR Radiance RGBE', source=source['sourceUrl'],
        authors=source['authors'], license='CC0-1.0', licenseUrl=source['licenseUrl'],
        sha256=sha(folder/'sky_1k.hdr'),
        sunPixelTopLeft=[609,119],
        note='Static distant sky; lower hemisphere is an artist-supplied extension. '
             'World rotation, exposure, fog and lighting belong to the consuming scene.')
    (folder / 'environment.json').write_text(json.dumps(sky, indent=2)+'\n')
    items.append(dict(id=sky['id'], type='hdr-environment',
                      manifest='environments/kloofendal-partly-cloudy/environment.json'))
    # Model manifests can be added independently without coupling them to this engine.
    for path in sorted((LIBRARY/'models').glob('**/asset.json')):
        asset=json.loads(path.read_text())
        items.append(dict(id=asset['id'],type=asset.get('type','gltf-model'),manifest=path.relative_to(LIBRARY).as_posix()))
    catalog = dict(schemaVersion=1, title='Cinder portable environment and vehicle assets',
        units='metres', models='glTF 2.0 / GLB, right handed, +Y up',
        runtimeDependencies=[], assets=items,
        exclusions=['Temporary Porsche personal-project exhaust samples are not part of this portable environment library.'],
        adapters='Game-specific lighting, terrain mixing and instancing are in showcase/; '
                 'no threepp binary, shader or C++ header is required to use these source assets.')
    (LIBRARY/'catalog.json').write_text(json.dumps(catalog,indent=2)+'\n')
    output=ROOT/'build/fidelity-v1/Cinder-Environment-Assets.zip'
    output.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(LIBRARY.rglob('*')):
            if path.is_file(): archive.write(path, 'cinder-environment/'+path.relative_to(LIBRARY).as_posix())
    print(json.dumps(dict(catalog=str(LIBRARY/'catalog.json'),archive=str(output),
                          assets=len(items),archiveSha256=sha(output)),indent=2))


if __name__ == '__main__':
    main()
