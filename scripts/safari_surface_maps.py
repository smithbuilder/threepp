"""Original, deterministic Safari enamel and body-local dry trail dust.

CPU-only NumPy/Pillow material authoring. No image/reference pixels are read.
``maps()`` returns glTF base-colour, metallic/roughness and tangent normal PNGs.
Use paint roughnessFactor=1, metallicFactor=0 and normalTexture.scale=.12.
This keeps the roughness values in the texture meaningful instead of multiplying
them by an unrelated material factor. Clearcoat remains a separate response.
"""
from __future__ import annotations

import io
from pathlib import Path

import numpy as np
from PIL import Image

SIZE = 512
SEED = 1207
PAINT_RGB = np.array([218.0, 210.0, 188.0])
SIDE_HEIGHT = 1.35
SIDE_Z_MIN = -2.32
SIDE_Z_SPAN = 4.62


def _png(rgba: np.ndarray) -> bytes:
    output = io.BytesIO()
    Image.fromarray(np.clip(np.rint(rgba), 0, 255).astype(np.uint8), 'RGBA').save(
        output, format='PNG', optimize=True)
    return output.getvalue()


def _periodic_field(size: int, seed: int, low: float, high: float) -> np.ndarray:
    """Band-limited periodic random field, normalized without sine motifs."""
    rng = np.random.default_rng(seed)
    noise = rng.standard_normal((size - 1, size - 1))
    freq = np.fft.fftfreq(size - 1) * (size - 1)
    fy, fx = np.meshgrid(freq, freq, indexing='ij')
    radius = np.sqrt(fx * fx + fy * fy)
    band = np.exp(-(radius / high) ** 4)
    if low > 0:
        band *= 1.0 - np.exp(-(radius / low) ** 4)
    band[0, 0] = 0
    field = np.fft.ifft2(np.fft.fft2(noise) * band).real
    field /= max(float(np.std(field)), 1e-12)
    field = np.tanh(field * .55)
    # Duplicate the opposite edge exactly: wrapping never exposes an atlas seam.
    return np.pad(field, ((0, 1), (0, 1)), mode='wrap')


def _arrays() -> list[np.ndarray]:
    broad = _periodic_field(SIZE, SEED, 0, 4)
    finish = _periodic_field(SIZE, SEED + 1, 24, 88)
    fine = _periodic_field(SIZE, SEED + 2, 80, 180)

    # Intact enamel stays almost uniform. Surface response supplies the detail,
    # rather than baking fake illumination or noisy grey grunge into the colour.
    albedo = np.empty((SIZE, SIZE, 4))
    albedo[..., :3] = PAINT_RGB + (
        broad * 1.25 + finish * .38 + fine * .18)[..., None]
    albedo[..., 3] = 255

    # glTF ORM: R=unoccluded, G=perceptual roughness, B=dielectric metalness.
    # Most enamel is .31-.35 rough; clearcoat adds a distinct smooth top lobe.
    orm = np.empty((SIZE, SIZE, 4))
    orm[..., 0] = 255
    orm[..., 1] = 84 + broad * 5.0 + finish * 3.5 + fine * 1.0
    orm[..., 2] = 0
    orm[..., 3] = 255

    # Very fine orange peel, no low-frequency height: broad panel reflections
    # must remain smooth. Wrapped central differences avoid a normal-map edge.
    height = finish * .090 + fine * .018
    core = height[:-1, :-1]
    dx = (np.roll(core, -1, axis=1) - np.roll(core, 1, axis=1)) * .5
    dy = (np.roll(core, -1, axis=0) - np.roll(core, 1, axis=0)) * .5
    normal = np.dstack([-dx, -dy, np.ones_like(core)])
    normal /= np.linalg.norm(normal, axis=2)[..., None]
    normal = np.pad(normal, ((0, 1), (0, 1), (0, 0)), mode='wrap')
    normal = np.dstack([(normal * .5 + .5) * 255,
                         np.full((SIZE, SIZE), 255.0)])
    return [albedo, orm, normal]


def maps() -> list[bytes]:
    """Return original 512px RGBA base colour, ORM and tangent normal PNGs."""
    return [_png(array) for array in _arrays()]


def _value_noise(points: np.ndarray, scale: float, seed: int) -> np.ndarray:
    """Continuous world-space value noise, shared across adjacent mesh patches."""
    sample = points * scale
    cell = np.floor(sample).astype(np.int64)
    frac = sample - cell
    weight = frac * frac * (3.0 - 2.0 * frac)
    result = np.zeros(len(points))
    mask = np.uint64(0xffffffff)
    for x in (0, 1):
        for y in (0, 1):
            for z in (0, 1):
                corner = (cell + [x, y, z]).astype(np.uint64)
                hashed = ((corner[:, 0] * np.uint64(73856093)) ^
                          (corner[:, 1] * np.uint64(19349663)) ^
                          (corner[:, 2] * np.uint64(83492791)) ^ np.uint64(seed)) & mask
                hashed ^= hashed >> np.uint64(16)
                hashed = (hashed * np.uint64(2246822519)) & mask
                hashed ^= hashed >> np.uint64(13)
                value = hashed.astype(np.float64) / float(0xffffffff)
                blend = np.prod(np.where([x, y, z], weight, 1 - weight), axis=1)
                result += value * blend
    return result


def _dust_coverage(points: np.ndarray) -> np.ndarray:
    points = np.asarray(points, dtype=np.float64)
    if points.ndim != 2 or points.shape[1] != 3 or not np.isfinite(points).all():
        raise ValueError('weather_colors requires finite Nx3 body coordinates')
    if len(points) == 0:
        return np.empty(0)
    height = points[:, 1]
    low = np.clip((1.06 - height) / .71, 0.0, 1.0)
    low = low * low * (3.0 - 2.0 * low)
    axle = np.maximum(np.exp(-((points[:, 2] - 1.35) / .69) ** 2),
                      np.exp(-((points[:, 2] + 1.35) / .69) ** 2))
    broad = _value_noise(points, 3.7, 5103)
    fine = _value_noise(points, 17.0, 7741)
    # Irregular, height-weighted deposits; never a global sine stripe or random
    # black speckle sprayed over otherwise clean roof/bonnet paint.
    deposits = np.clip((broad * .80 + fine * .20 - .20) / .68, 0.0, 1.0)
    return np.clip(low * (.30 + .70 * deposits) * (.46 + .54 * axle) * .76, 0.0, .70)


def weather_colors(points: np.ndarray) -> np.ndarray:
    """Linear vertex-colour multiplier: clean upper body, dry dirt at the sills.

    Coordinates are the generator's metres (+Y up, +Z forward). Coverage uses
    physical height and distance to both axle zones. It does not depend on UVs,
    so top/side patches meet without colour seams or repeated texture bands.
    """
    dust = _dust_coverage(points)
    tint = np.array([.56, .49, .37])
    colours = np.ones((len(points), 4))
    colours[:, :3] = 1 - dust[:, None] * (1 - tint)
    return colours.astype(np.float32)


def side_uv(points: np.ndarray) -> np.ndarray:
    """UV for the two side skins; pixel-centre inset prevents repeat seams."""
    points = np.asarray(points)
    uv = np.c_[(points[:, 2] - SIDE_Z_MIN) / SIDE_Z_SPAN,
               points[:, 1] / SIDE_HEIGHT]
    return (np.clip(uv, 0, 1) * (1 - 1 / SIZE) + .5 / SIZE).astype(np.float32)


def side_maps() -> list[bytes]:
    """Side enamel/dust maps with physically linked colour, roughness and coat.

    R in the ORM image is a clearcoat amount mask (not AO); G is roughness and
    B is metalness. Bind that same ORM texture as KHR clearcoatTexture. It is
    valid because this material does not use an occlusionTexture. No extra
    clearcoat mask image or runtime shader is needed.
    """
    arrays = _arrays()
    z, y = np.meshgrid(np.linspace(SIDE_Z_MIN, SIDE_Z_MIN + SIDE_Z_SPAN, SIZE),
                       np.linspace(0, SIDE_HEIGHT, SIZE))
    points = np.c_[np.full(z.size, 1.04), y.ravel(), z.ravel()]
    dust = _dust_coverage(points).reshape(SIZE, SIZE)
    # Apply the same tint in linear light. These sides must not also carry the
    # weather vertex colours, or deposits would be counted twice.
    base = arrays[0][..., :3] / 255
    linear = np.where(base <= .04045, base / 12.92,
                      ((base + .055) / 1.055) ** 2.4)
    tint = weather_colors(points)[:, :3].reshape(SIZE, SIZE, 3)
    linear *= tint
    srgb = np.where(linear <= .0031308, linear * 12.92,
                    1.055 * linear ** (1 / 2.4) - .055)
    arrays[0][..., :3] = srgb * 255
    # A dry deposit masks the smooth paint top-coat and diffuses its highlight.
    coverage = np.clip(dust / .70, 0, 1)
    arrays[1][..., 0] = (1 - coverage) ** 2 * 255
    arrays[1][..., 1] = np.clip(arrays[1][..., 1] + coverage * 105, 0, 255)
    return [_png(array) for array in arrays]


def write_previews(output: Path) -> None:
    """Save clearly labelled CPU texture evidence; no native shading implied."""
    output.mkdir(parents=True, exist_ok=True)
    for name, data in zip(('enamel-albedo', 'enamel-orm', 'enamel-normal'), maps()):
        (output / f'{name}.png').write_bytes(data)
    for name, data in zip(('side-albedo', 'side-roughness-coat', 'side-normal'), side_maps()):
        (output / f'{name}.png').write_bytes(data)
    # Side panel: +/-2.32m longitudinally, .3..1.65m high at x=1.02m.
    z, y = np.meshgrid(np.linspace(2.32, -2.32, SIZE), np.linspace(1.65, .3, 256))
    p = np.c_[np.full(z.size, 1.02), y.ravel(), z.ravel()]
    linear_base = np.where(PAINT_RGB / 255 <= .04045, PAINT_RGB / 255 / 12.92,
                           ((PAINT_RGB / 255 + .055) / 1.055) ** 2.4)
    shaded = weather_colors(p)[:, :3] * linear_base
    srgb = np.where(shaded <= .0031308, shaded * 12.92, 1.055 * shaded ** (1 / 2.4) - .055)
    rgba = np.dstack([srgb.reshape(256, SIZE, 3) * 255, np.full((256, SIZE), 255)])
    (output / 'body-local-dust-colour-study.png').write_bytes(_png(rgba))


if __name__ == '__main__':
    write_previews(Path(__file__).resolve().parents[1] / 'build/safari-material-study')
