"""Original, deterministic Safari enamel and body-local dry trail dust.

CPU-only NumPy/Pillow material authoring using an original built-in image_gen
enamel/wear bitmap. No user reference or manufacturer pixels are sampled.
``maps()`` returns glTF base-colour, metallic/roughness and tangent normal PNGs.
Use paint roughnessFactor=1, metallicFactor=0 and normalTexture.scale=.12.
This keeps the roughness values in the texture meaningful instead of multiplying
them by an unrelated material factor. Clearcoat remains a separate response.
"""
from __future__ import annotations

import io
from functools import lru_cache
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

SIZE = 512
ALBEDO_SIZE = 1024
SEED = 1207
PAINT_RGB = np.array([218.0, 210.0, 188.0])
SIDE_HEIGHT = 1.35
SIDE_Z_MIN = -2.32
SIDE_Z_SPAN = 4.40
DUST_TINT = np.array([.40, .31, .20])
GENERATED_ALBEDO = Path(__file__).resolve().parents[1] / 'showcase/assets/safari-enamel-wear-v1.png'
# The upright end panels need XY domains. A top projection has zero UV area on
# these panels and stretches a single texture row into vertical colour/coat
# stripes. These metre bounds include the rendered returns without wrapping.
FASCIA_BOUNDS = {
    'front': dict(x_min=-1.10, x_span=2.20, y_min=.70, y_span=.60, z=2.08),
    'rear': dict(x_min=-.92, x_span=1.84, y_min=.73, y_span=.63, z=-2.32),
}


@lru_cache(maxsize=1)
def _wear_source() -> np.ndarray:
    """Fine chips/scratches isolated from the immutable original bitmap.

    The source's broad photographic patina is not paint albedo. Removing a
    roughly13mm local background retains small damage without copying cloudy
    illumination into enamel. Normals never come from this image luminance.
    """
    with Image.open(GENERATED_ALBEDO) as image:
        rgb = image.convert('RGB')
        source = np.asarray(rgb, dtype=np.float64)
        background = np.asarray(rgb.filter(ImageFilter.GaussianBlur(8)), dtype=np.float64)
    return np.clip(np.minimum(source - background + 2.5, 0), -175, 0)


def _sample_wear(size: int, domain: str) -> tuple[np.ndarray, np.ndarray]:
    """Sample roughly two-metre paint history tiles at the body atlas scale."""
    source = _wear_source()
    u, v = np.meshgrid(np.linspace(0, 1, size), np.linspace(0, 1, size))
    if domain == 'side':
        u, v = u * (SIDE_Z_SPAN / 2.0) + .117, v * (SIDE_HEIGHT / 2.0) + .213
    elif domain == 'top':
        u, v = u * 1.10 + .373, v * (SIDE_Z_SPAN / 2.0) + .087
    elif domain in FASCIA_BOUNDS:
        bounds = FASCIA_BOUNDS[domain]
        # Both axes consume the source at the same two-metre material scale;
        # the square image is an atlas, not a square physical body panel.
        offset = (.293, .411) if domain == 'front' else (.617, .139)
        u = (bounds['x_min'] + u * bounds['x_span']) / 2.0 + offset[0]
        v = (bounds['y_min'] + v * bounds['y_span']) / 2.0 + offset[1]
    elif domain != 'clean':
        raise ValueError('Unknown paint detail domain')
    # Bilinear wrapped sampling. The generated borders differ by only a few
    # colour levels; texture detail is not repeated as a high-contrast decal.
    x = np.mod(u, 1) * (source.shape[1] - 1)
    y = np.mod(v, 1) * (source.shape[0] - 1)
    x0, y0 = np.floor(x).astype(int), np.floor(y).astype(int)
    x1, y1 = (x0 + 1) % source.shape[1], (y0 + 1) % source.shape[0]
    fx, fy = (x - x0)[..., None], (y - y0)[..., None]
    detail = ((source[y0, x0] * (1 - fx) + source[y0, x1] * fx) * (1 - fy) +
              (source[y1, x0] * (1 - fx) + source[y1, x1] * fx) * fy)
    wear = np.clip(np.max(-detail, axis=2) / 48.0, 0, 1)
    return detail, wear


def _use_pattern(size: int, domain: str) -> np.ndarray:
    """Stone damage is concentrated at leading edges and wheel-opening lips."""
    u, v = np.meshgrid(np.linspace(0, 1, size), np.linspace(0, 1, size))
    z = SIDE_Z_MIN + v * SIDE_Z_SPAN if domain == 'top' else SIDE_Z_MIN + u * SIDE_Z_SPAN
    if domain == 'top':
        axle = np.maximum(np.exp(-((z - 1.35) / .60) ** 2), np.exp(-((z + 1.35) / .60) ** 2))
        shoulders = np.exp(-((np.abs(u * 2 - 1) - .87) / .16) ** 2) * axle
        leading = np.exp(-((z - 1.99) / .12) ** 2)
        bonnet = [(-.56,.78),(.56,.78),(.62,1.008),(.60,1.715),(.52,1.96),
                  (-.52,1.96),(-.60,1.715),(-.62,1.008)]
        x = (u * 2 - 1) * _body_width(z)
        seam = np.exp(-(_distance_loop(np.c_[x.ravel(), z.ravel()], bonnet).reshape(size,size) / .012) ** 2)
        return .035 + .70 * shoulders + .72 * leading + .34 * seam
    if domain == 'side':
        y = v * SIDE_HEIGHT
        distance = np.minimum(*[np.abs(np.sqrt((z - a) ** 2 + (y - .41) ** 2) - .655)
                                for a in (-1.35, 1.35)])
        lip = np.exp(-(distance / .085) ** 2)
        handle = np.sqrt(((z + .425) / .118) ** 2 + ((y - 1.08) / .036) ** 2)
        handled_edge = np.exp(-((handle - 1) / .17) ** 2)
        return .035 + .85 * lip + .30 * np.clip((.58-y)/.24,0,1) + .48 * handled_edge
    if domain in FASCIA_BOUNDS:
        points = _fascia_points(size, domain)
        _, exposure = _fascia_deposits(points, domain)
        # Keep nearly all broad upper enamel intact. Original chips become
        # more frequent only on exposed lower edges and the outer corners.
        return (.10 + .68 * exposure).reshape(size, size)
    return np.ones((size, size))


def _add_generated_detail(arrays: list[np.ndarray], domain: str,
                          strength: float, albedo_size: int = ALBEDO_SIZE) -> list[np.ndarray]:
    """Colour chips/patina drive matching roughness and clearcoat, not height."""
    if albedo_size != arrays[0].shape[0]:
        albedo = np.asarray(Image.fromarray(np.clip(np.rint(arrays[0]), 0, 255).astype(np.uint8), 'RGBA').resize(
            (albedo_size, albedo_size), Image.Resampling.LANCZOS), dtype=np.float64)
    else:
        albedo = arrays[0].copy()
    detail, _ = _sample_wear(albedo_size, domain)
    use = _chip_use(detail, _use_pattern(albedo_size, domain))
    albedo[..., :3] = np.clip(albedo[..., :3] + detail * (strength * use)[..., None], 0, 255)
    arrays[0] = albedo
    detail, wear = _sample_wear(arrays[1].shape[0], domain)
    wear = np.clip(wear * strength * _chip_use(
        detail, _use_pattern(arrays[1].shape[0], domain)), 0, 1)
    arrays[1][..., 0] *= 1 - wear * .88
    arrays[1][..., 1] = np.clip(arrays[1][..., 1] + wear * 54, 0, 245)
    return arrays


def _chip_use(detail: np.ndarray, use: np.ndarray) -> np.ndarray:
    """A few deep source chips survive on clean panels; pale patina does not.

    Only residuals darker than22 source code values may raise the existing
    clean-region use mask, and even those stop at.095. Broad enamel fields,
    dust deposits and the immutable source image remain unchanged.
    """
    strong = np.clip((np.max(-detail, axis=2) - 22.0) / 30.0, 0, 1)
    return np.maximum(use, .095 * strong)


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


def _arrays(generated_detail: bool = True) -> list[np.ndarray]:
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
    arrays = [albedo, orm, normal]
    return _add_generated_detail(arrays, 'clean', .35, SIZE) if generated_detail else arrays


def maps() -> list[bytes]:
    """Return 512px clean enamel maps with restrained original wear detail."""
    return [_png(array) for array in _arrays()]


def _value_noise(points: np.ndarray, scale: float, seed: int) -> np.ndarray:
    """Continuous world-space value noise, shared across adjacent mesh patches."""
    # A rotated slice through the 3D lattice avoids square, axis-aligned flecks
    # on planar body/case UVs while retaining exactly the same metre scale.
    cy,sy,cx,sx=np.cos(.61),np.sin(.61),np.cos(.37),np.sin(.37)
    basis=np.array([[cy,0,sy],[0,1,0],[-sy,0,cy]]) @ np.array([[1,0,0],[0,cx,-sx],[0,sx,cx]])
    sample = (points @ basis) * scale
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


def _distance_loop(points: np.ndarray, outline) -> np.ndarray:
    """Shortest physical distance to a closed seam, without a painted shadow."""
    loop = np.asarray(outline, dtype=np.float64)
    best = np.full(len(points), np.inf)
    for a, b in zip(loop, np.roll(loop, -1, axis=0)):
        delta = b - a
        t = np.clip((points-a) @ delta / max(float(delta @ delta),1e-15),0,1)
        best = np.minimum(best,np.linalg.norm(points-a-t[:,None]*delta,axis=1))
    return best


def _body_width(z: np.ndarray) -> np.ndarray:
    # Read the shared physical loft rather than an unrelated approximate width.
    from safari_body_shell import width
    return np.asarray(width(z))


def _dust_coverage(points: np.ndarray) -> np.ndarray:
    points = np.asarray(points, dtype=np.float64)
    if points.ndim != 2 or points.shape[1] != 3 or not np.isfinite(points).all():
        raise ValueError('weather_colors requires finite Nx3 body coordinates')
    if len(points) == 0:
        return np.empty(0)
    height, z = points[:,1], points[:,2]
    # Side atlas and conformed livery share exactly the same Y/Z field.
    q = np.c_[np.zeros(len(points)),height,z]
    grain = _value_noise(q,47,7741)
    speckle = np.clip((grain-.54)/.26,0,1)
    irregular = .42+.58*_value_noise(q,11,5103)
    low = np.clip((.93-height)/.48,0,1)
    sill = np.exp(-((height-.405)/.045)**2)
    lip = np.zeros(len(points)); spray = np.zeros(len(points))
    for axle in (-1.35,1.35):
        radius = np.hypot(z-axle,height-.41)
        lip = np.maximum(lip,np.exp(-((radius-.655)/.026)**2))
        # The fan trails the wheel toward -Z, instead of a cloud over the door.
        trailing = np.exp(-((z-(axle-.27))/.34)**2)
        spray = np.maximum(spray,trailing*np.clip((1.06-height)/.50,0,1))
    door=[(.52,1.158),(.565,1.10),(.575,.95),(.55,.69),(.48,.49),(.32,.47),
          (-.40,.47),(-.54,.50),(-.64,.75),(-.65,1.10),(-.60,1.145),(-.30,1.162),(.20,1.164)]
    seam=np.exp(-(_distance_loop(np.c_[z,height],door)/.009)**2)
    handle_wipe=np.exp(-((z+.425)/.145)**2-((height-1.08)/.060)**2)
    dust=(sill*.21+lip*.23)*irregular+(low*.20+spray*.28)*speckle+seam*.065*irregular
    return np.clip(dust*(1-handle_wipe*.85),0,.58)


def weather_colors(points: np.ndarray) -> np.ndarray:
    """Linear vertex-colour multiplier: clean upper body, dry dirt at the sills.

    Coordinates are the generator's metres (+Y up, +Z forward). Coverage uses
    physical height and distance to both axle zones. It does not depend on UVs,
    so top/side patches meet without colour seams or repeated texture bands.
    """
    dust = _dust_coverage(points)
    colours = np.ones((len(points), 4))
    colours[:, :3] = 1 - dust[:, None] * (1 - DUST_TINT)
    return colours.astype(np.float32)


def side_uv(points: np.ndarray) -> np.ndarray:
    """UV for the two side skins; pixel-centre inset prevents repeat seams."""
    points = np.asarray(points)
    uv = np.c_[(points[:, 2] - SIDE_Z_MIN) / SIDE_Z_SPAN,
               points[:, 1] / SIDE_HEIGHT]
    return (np.clip(uv, 0, 1) * (1 - 1 / SIZE) + .5 / SIZE).astype(np.float32)


def _fascia_points(size: int, domain: str) -> np.ndarray:
    bounds = FASCIA_BOUNDS[domain]
    x, y = np.meshgrid(np.linspace(bounds['x_min'], bounds['x_min'] + bounds['x_span'], size),
                       np.linspace(bounds['y_min'], bounds['y_min'] + bounds['y_span'], size))
    return np.c_[x.ravel(), y.ravel(), np.full(x.size, bounds['z'])]


def _fascia_uv(points: np.ndarray, domain: str) -> np.ndarray:
    points = np.asarray(points, dtype=np.float64)
    if points.ndim != 2 or points.shape[1] != 3 or not np.isfinite(points).all():
        raise ValueError('Fascia UVs require finite Nx3 body coordinates')
    bounds = FASCIA_BOUNDS[domain]
    uv = np.c_[(points[:, 0] - bounds['x_min']) / bounds['x_span'],
               (points[:, 1] - bounds['y_min']) / bounds['y_span']]
    return (np.clip(uv, 0, 1) * (1 - 1 / SIZE) + .5 / SIZE).astype(np.float32)


def front_uv(points: np.ndarray) -> np.ndarray:
    """Real-width/height XY atlas for body.rounded_front_valance only."""
    return _fascia_uv(points, 'front')


def rear_uv(points: np.ndarray) -> np.ndarray:
    """Real-width/height XY atlas for body.rounded_rear_valance.* only."""
    return _fascia_uv(points, 'rear')


def _fascia_deposits(points: np.ndarray, domain: str) -> tuple[np.ndarray, np.ndarray]:
    """Dry dirt coverage and stone exposure in actual body metres.

    The front collects leading-edge grit; the rear gets wheel-wake deposits at
    its outer corners and on the low ledge. Recess edges trap a small amount of
    dust. These are colour/finish masks, never baked illumination or black AO.
    """
    x, y = points[:, 0], points[:, 1]
    seed = 9121 if domain == 'front' else 9263
    broad = _value_noise(points, 8.5, seed)
    fine = _value_noise(points, 47.0, seed + 31)
    patch = np.clip((broad * .64 + fine * .36 - .31) / .52, 0, 1)
    if domain == 'front':
        low = np.clip((1.005 - y) / .255, 0, 1)
        corners = np.exp(-((np.abs(x) - .985) / .13) ** 2)
        lower_edge = np.exp(-((y - .755) / .035) ** 2)
        # The existing physical headlamp aperture radii are .174m. Dust stays
        # around the gasket seat instead of becoming a dark painted lamp disc.
        seat = np.zeros(len(points))
        for side in (-1, 1):
            radius = np.hypot(x - side * .89, y - 1.00)
            seat = np.maximum(seat, np.exp(-((radius - .190) / .016) ** 2))
        exposure = np.clip(low * .65 + corners * .35 + lower_edge * .30, 0, 1)
        dust = ((low * .19 + corners * low * .14 + lower_edge * .10) *
                (.22 + .78 * patch) + seat * (.018 + .055 * patch))
    else:
        low = np.clip((1.075 - y) / .31, 0, 1)
        wake = np.exp(-((np.abs(x) - .845) / .135) ** 2)
        lower_edge = np.exp(-((y - .775) / .035) ** 2)
        # Distance to the real rear-band recess boundary (x+/-.76,
        # y.84..1.045), including its corners, in metres.
        dx = np.maximum(np.abs(x) - .76, 0)
        dy = np.maximum(np.maximum(.84 - y, y - 1.045), 0)
        outside = np.hypot(dx, dy)
        inside = np.minimum(.76 - np.abs(x), np.minimum(y - .84, 1.045 - y))
        distance = np.where((dx == 0) & (dy == 0), np.maximum(inside, 0), outside)
        recess_edge = np.exp(-(distance / .012) ** 2)
        exposure = np.clip(wake * (.42 + .40 * low) + lower_edge * .42, 0, 1)
        dust = ((wake * (.075 + .21 * low) + lower_edge * .14) *
                (.22 + .78 * patch) + recess_edge * (.015 + .065 * patch))
    return np.clip(dust, 0, .48), exposure


def _fascia_maps(domain: str) -> list[bytes]:
    arrays = _arrays(False)
    dust, _ = _fascia_deposits(_fascia_points(SIZE, domain), domain)
    dust = dust.reshape(SIZE, SIZE)
    clean = _srgb_to_linear(arrays[0][..., :3])
    dry_dirt = _srgb_to_linear([121, 101, 70])
    arrays[0][..., :3] = _linear_to_srgb(clean * (1 - dust[..., None]) +
                                       dry_dirt * dust[..., None])
    roughness = arrays[1][..., 1] / 255
    arrays[1][..., 0] = (1 - dust) ** 2 * 255
    arrays[1][..., 1] = (roughness + (.82 - roughness) * dust) * 255
    # Return the existing restrained enamel normal unchanged. The generator
    # can reuse texture2 and append only the new base/packed-mask pair.
    return [_png(array) for array in _add_generated_detail(arrays, domain, .78)]


def front_maps() -> list[bytes]:
    """Front fascia base1024 / coat-R rough-G metal-B512 / enamel normal512.

    Use only with front_uv, white base, roughnessFactor1 and metalness0. Bind
    the packed map as both metallicRoughnessTexture and clearcoatTexture, and
    remove additional vertex dust on these already weathered atlas surfaces.
    """
    return _fascia_maps('front')


def rear_maps() -> list[bytes]:
    """Rear fascia pair/normal with rear_uv; same material contract as front."""
    return _fascia_maps('rear')


def side_maps() -> list[bytes]:
    """Side enamel/dust maps with physically linked colour, roughness and coat.

    R in the ORM image is a clearcoat amount mask (not AO); G is roughness and
    B is metalness. Bind that same ORM texture as KHR clearcoatTexture. It is
    valid because this material does not use an occlusionTexture. No extra
    clearcoat mask image or runtime shader is needed.
    """
    arrays = _arrays(False)
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
    coverage = np.clip(dust, 0, 1)
    arrays[1][..., 0] = (1 - coverage) ** 2 * 255
    arrays[1][..., 1] += (.85*255-arrays[1][...,1])*coverage
    return [_png(array) for array in _add_generated_detail(arrays, 'side', .95)]


def _srgb_to_linear(rgb: np.ndarray) -> np.ndarray:
    rgb = np.asarray(rgb, dtype=np.float64) / 255
    return np.where(rgb <= .04045, rgb / 12.92, ((rgb + .055) / 1.055) ** 2.4)


def _linear_to_srgb(rgb: np.ndarray) -> np.ndarray:
    rgb = np.clip(rgb, 0, 1)
    return np.where(rgb <= .0031308, rgb * 12.92, 1.055 * rgb ** (1 / 2.4) - .055) * 255


def flare_maps() -> list[bytes]:
    """Used charcoal flare: actual arch-angle/radial-width UV, not body paint.

    Bind only arch.flare_shell parts whose U=angle/pi and V=radial fraction.
    Material base white, roughnessFactor1, metal0; return base/ORM/normal512.
    Raised edges show rubbed grey primer, crevices retain packed brown dirt.
    """
    u, v = np.meshgrid(np.linspace(0, 1, SIZE), np.linspace(0, 1, SIZE))
    angle = u * np.pi
    radius = .615 + v * .105
    points = np.c_[v.ravel() * .105,
                    (.41 + radius * np.sin(angle)).ravel(),
                    (radius * np.cos(angle)).ravel()]
    broad = _value_noise(points, 18.0, 2801).reshape(SIZE, SIZE)
    grain = _value_noise(points, 130.0, 2819).reshape(SIZE, SIZE)
    low = (1 - np.sin(angle)) ** .8
    inner = np.exp(-((v - .04) / .13) ** 2)
    # Bolt crevices are in physical metres, so each ring remains small rather
    # than a large polka-dot graphic once the long, narrow flare is unwrapped.
    bolt_crevice = np.zeros((SIZE, SIZE))
    for bolt_angle in np.linspace(.10, np.pi - .10, 11):
        distance = np.sqrt(((angle - bolt_angle) * .688) ** 2 + ((v - .695) * .105) ** 2)
        bolt_crevice = np.maximum(bolt_crevice, np.exp(-((distance - .012) / .006) ** 2))
    fleck = np.clip((grain-.54)/.28,0,1)
    dust = np.clip((.19*low+.17*inner+.20*bolt_crevice)*(.38+.62*broad)+low*fleck*.20,0,.58)
    rubbed = np.exp(-((v - .965) / .034) ** 2) * np.clip((broad - .34) / .40, 0, 1)
    _, original_chips = _sample_wear(SIZE, 'clean')
    rubbed = np.maximum(rubbed, original_chips * (.10 + .10 * low))
    clean = _srgb_to_linear([38, 44, 42])
    dry_dirt = _srgb_to_linear([120, 99, 66])
    grey_primer = _srgb_to_linear([101, 106, 99])
    linear = clean + dust[..., None] * (dry_dirt - clean)
    linear = linear * (1 - rubbed[..., None] * .60) + grey_primer * rubbed[..., None] * .60
    albedo = np.dstack([_linear_to_srgb(linear), np.full((SIZE, SIZE), 255)])
    orm = np.empty_like(albedo)
    orm[..., 0] = 255
    orm[..., 1] = np.clip((.66 + .25 * dust - .10 * rubbed + (grain - .5) * .035) * 255, 0, 255)
    orm[..., 2] = 0
    orm[..., 3] = 255
    # 35-micrometre coating grain; slopes use the physical arc/flare width. This
    # does not turn the plastic/paint into a rugged displaced rock surface.
    height = (grain - .5) * .000035
    dy, dx = np.gradient(height, .105 / (SIZE - 1), np.pi * .67 / (SIZE - 1))
    normal = np.dstack([-dx, -dy, np.ones_like(height)])
    normal /= np.linalg.norm(normal, axis=2)[..., None]
    normal = np.dstack([(normal * .5 + .5) * 255, np.full((SIZE, SIZE), 255)])
    return [_png(array) for array in (albedo, orm, normal)]


def hardware_finish(kind: str) -> dict:
    """Standard-PBR finish and physical grain scale; no extra texture or lobe.

    Existing grain image4 has about51.2 fine periods per tile. UV scales below
    put those periods near.25..1mm, rather than the previous centimetre grain.
    """
    finishes={
        'coated_steel':(.48,0.,.08,32.), 'case':(.52,0.,.12,32.),
        'canvas':(.93,0.,.18,24.), 'exhaust':(.35,.96,.045,64.),
        'cast_alloy':(.67,.90,.12,40.), 'trim':(.76,0.,.10,32.),
        'painted_steel':(.45,0.,.07,32.), 'recovery_board':(.73,0.,.12,32.),
        'rubber':(.82,0.,.14,24.),
    }
    if kind not in finishes:raise ValueError('Unknown hardware finish: '+kind)
    rough,metal,normal,uv=finishes[kind]
    return dict(roughness=rough,metalness=metal,normal_scale=normal,uv_scale=uv)


def webbing_base_color(original_srgb: int) -> list[float]:
    """Linear factor for existing webbing material copies; no new image.

    Orange restraint is darker than the molded recovery boards. Black loops
    remain charcoal. Apply to the canvas material copy, never its source.
    """
    rgb = [156, 84, 35] if original_srgb == 0xcc6d27 else [32, 38, 34]
    return _srgb_to_linear(rgb).tolist() + [1.0]


def hardware_uv(points: np.ndarray, normals: np.ndarray, kind: str) -> np.ndarray:
    """Dominant-plane world UVs in metres, with a submillimetre grain repeat."""
    points=np.asarray(points,float);normals=np.asarray(normals,float)
    if points.ndim!=2 or points.shape[1]!=3 or normals.shape!=points.shape:
        raise ValueError('Hardware UVs need matching Nx3 positions/normals')
    if not np.isfinite(points).all() or not np.isfinite(normals).all():
        raise ValueError('Hardware UV inputs must be finite')
    axis=np.argmax(np.abs(normals),axis=1);uv=np.empty((len(points),2))
    for normal_axis,plane in ((0,(2,1)),(1,(0,2)),(2,(0,1))):
        select=axis==normal_axis;uv[select]=points[select][:,plane]
    return (uv*hardware_finish(kind)['uv_scale']).astype(np.float32)


def hardware_weather_colors(points: np.ndarray, kind: str,
                            normals: np.ndarray | None = None,
                            part_name: str = '', component_bounds: dict | None = None) -> np.ndarray:
    """Absolute linear vertex colours for selected white-base hardware copies.

    Apply hardware_finish(kind), replace baseColorFactor RGB with white and
    enable these vertex colours. Do not apply as multipliers to
    already-black materials. The exhaust tint is an artistic heat-history cue,
    not a thermodynamic temperature prediction; actual soot cavities stay mesh.
    """
    points = np.asarray(points, dtype=np.float64)
    if points.ndim != 2 or points.shape[1] != 3 or not np.isfinite(points).all():
        raise ValueError('hardware_weather_colors requires finite Nx3 points')
    if normals is None:
        upward = np.full(len(points), .45)
    else:
        normals = np.asarray(normals, dtype=np.float64)
        if normals.shape != points.shape or not np.isfinite(normals).all():
            raise ValueError('Hardware normals must match the finite Nx3 points')
        upward = np.clip((normals[:, 1] + .1) / 1.1, 0, 1)
    defaults = {'coated_steel': [32, 42, 40], 'case': [108, 111, 86],
                'canvas': [88, 84, 68], 'exhaust': [146, 148, 141],
                'cast_alloy': [150, 155, 147], 'trim':[37,43,41],
                'painted_steel':[181,60,46], 'recovery_board':[204,109,39],
                'rubber':[35,40,37]}
    if kind not in defaults:
        raise ValueError('Unknown Safari hardware material kind: ' + kind)
    if len(points) == 0:
        return np.empty((0, 4), dtype=np.float32)
    broad = _value_noise(points, 17.0, 6319)
    fine = _value_noise(points, 34.0, 6449)
    base = np.broadcast_to(_srgb_to_linear(defaults[kind]), (len(points), 3)).copy()
    dust_colour = _srgb_to_linear([119, 101, 72])
    if kind=='trim':
        return np.c_[base,np.ones(len(points))].astype(np.float32)
    if component_bounds is not None:
        lower=np.asarray(component_bounds['min'],float);upper=np.asarray(component_bounds['max'],float)
        if lower.shape!=(3,) or upper.shape!=(3,) or not np.isfinite([lower,upper]).all() or np.any(upper<lower):
            raise ValueError('component_bounds needs finite min/max XYZ vectors')
    else:lower,upper=points.min(0),points.max(0)
    distance=np.maximum(np.minimum(points-lower,upper-points),0)
    # A surface point has one zero distance; its second closest box plane is
    # the physical edge. Whole-item bounds prevent every case rib being worn.
    edge=np.exp(-(np.sort(distance,axis=1)[:,1]/.013)**2)
    handled=float(any(word in part_name for word in ('handle','latch','filler','runner','strap')))
    fleck=np.clip((fine-.52)/.30,0,1)
    if kind in ('coated_steel', 'cast_alloy'):
        low = np.clip((.95 - points[:, 1]) / .70, 0, 1)
        dust = (low * .20 + upward * .045) * (.30 + .70 * fleck)
        base = base * (1 - dust[:, None]) + dust_colour * dust[:, None]
        if kind=='coated_steel':
            # Primer rub belongs at real tie-down contact bands on rack rails.
            tie=np.maximum(np.exp(-((points[:,2]+.39)/.021)**2),np.exp(-((points[:,2]-.31)/.021)**2))
            rub=tie*upward*np.clip((fine-.48)/.32,0,1)*.22 if part_name.startswith('rack.') else np.zeros(len(points))
            base=base*(1-rub[:,None])+_srgb_to_linear([95,102,96])*rub[:,None]
        if kind == 'cast_alloy':
            oil = np.clip((.51 - points[:, 1]) / .22, 0, 1) * (.10 + fine * .28)
            base *= 1 - oil[:, None] * .62
    elif kind in ('case', 'canvas'):
        dust = (.035*upward+.14*edge)*(.35+.65*fleck)
        base = base * (1 - dust[:, None]) + dust_colour * dust[:, None]
        if kind == 'case':
            rub = (edge*.22+handled*.10)*np.clip((fine-.43)/.35,0,1)
            base = base * (1 - rub[:, None]) + _srgb_to_linear([149, 145, 116]) * rub[:, None]
        else:
            fade=edge*(.08+.10*broad)
            base=base*(1-fade[:,None])+_srgb_to_linear([103,107,88])*fade[:,None]
    elif kind in ('painted_steel','recovery_board','rubber'):
        dust=(upward*.045+edge*.10)*(.30+.70*fleck)
        base=base*(1-dust[:,None])+dust_colour*dust[:,None]
        rub=(edge*.40+handled*.18)*np.clip((fine-.50)/.32,0,1)
        target={'painted_steel':[107,111,102],'recovery_board':[225,145,65],'rubber':[67,72,65]}[kind]
        base=base*(1-rub[:,None])+_srgb_to_linear(target)*rub[:,None]
    else:
        # Headers are upstream near z=-1.2..-1.9; the separate rear silencer is
        # z=-2.19 and open tips end near -2.70. Moderate straw/blue heat bands
        # belong near header junctions, while the rear tips remain satin steel.
        hot = np.exp(-((points[:, 2] + 1.66) / .43) ** 2)
        straw = hot * (.18 + .26 * broad)
        base = base * (1 - straw[:, None]) + _srgb_to_linear([156, 126, 84]) * straw[:, None]
        blue = np.exp(-((points[:, 2] + 1.91) / .10) ** 2) * .18
        base = base * (1 - blue[:, None]) + _srgb_to_linear([108, 117, 139]) * blue[:, None]
        soot = np.clip((-points[:, 2] - 2.61) / .09, 0, 1) * (.12 + .18 * fine)
        base *= 1 - soot[:, None] * .75
        dust = upward * .08 * broad
        base = base * (1 - dust[:, None]) + dust_colour * dust[:, None]
    return np.c_[np.clip(base, 0, 1), np.ones(len(points))].astype(np.float32)


def top_maps() -> list[bytes]:
    """Original hood/shoulder wear for the continuous upper shell's existing UV.

    U is lateral normalized body width and V is z=-2.32..2.08m. This pair is
    assigned only to that shell, never to the roof, glass, or default-planar UV
    accessories. Base colour and packed roughness/clearcoat share the mask.
    """
    arrays = _arrays(False)
    u, v = np.meshgrid(np.linspace(0, 1, SIZE), np.linspace(0, 1, SIZE))
    z = SIDE_Z_MIN + v * SIDE_Z_SPAN
    t = u * 2 - 1
    w = _body_width(z)
    x = t * w
    points = np.c_[x.ravel(), np.full(z.size, 1.08), z.ravel()]
    grain = _value_noise(points,47,9127).reshape(SIZE,SIZE)
    speckle = np.clip((grain-.55)/.24,0,1)
    axle = np.maximum(np.exp(-((z-1.12)/.30)**2),np.exp(-((z+1.60)/.28)**2))
    shoulder = np.exp(-((np.abs(x)-.97)/.14)**2)*axle
    leading = np.exp(-((z-2.02)/.075)**2)
    bonnet=[(-.56,.78),(.56,.78),(.62,1.008),(.60,1.715),(.52,1.96),
             (-.52,1.96),(-.60,1.715),(-.62,1.008)]
    lid=[(-.53,-1.67),(.53,-1.67),(.53,-2.13),(-.53,-2.13)]
    seam=np.minimum(_distance_loop(points[:,[0,2]],bonnet),
                    _distance_loop(points[:,[0,2]],lid)).reshape(SIZE,SIZE)
    seam=np.exp(-(seam/.010)**2)
    # Broad bonnet/deck panels stay intact. Dirt is a narrow seam deposit or
    # discrete leading-edge/shoulder spray, not a low-frequency grey cloud.
    dust=np.clip((shoulder*.30+leading*.24)*speckle+seam*(.018+.055*grain),0,.45)

    base = arrays[0][..., :3] / 255
    linear = np.where(base <= .04045, base / 12.92,
                      ((base + .055) / 1.055) ** 2.4)
    linear *= 1 - dust[..., None] * (1 - DUST_TINT)
    srgb = np.where(linear <= .0031308, linear * 12.92,
                    1.055 * linear ** (1 / 2.4) - .055)
    arrays[0][..., :3] = srgb * 255
    coverage = np.clip(dust, 0, 1)
    arrays[1][..., 0] = (1 - coverage) ** 2 * 255
    arrays[1][..., 1] += (.85*255-arrays[1][...,1])*coverage
    return [_png(array) for array in _add_generated_detail(arrays, 'top', 1.05)[:2]]


def write_previews(output: Path) -> None:
    """Save clearly labelled CPU texture evidence; no native shading implied."""
    output.mkdir(parents=True, exist_ok=True)
    for name, data in zip(('enamel-albedo', 'enamel-orm', 'enamel-normal'), maps()):
        (output / f'{name}.png').write_bytes(data)
    for name, data in zip(('side-albedo', 'side-roughness-coat', 'side-normal'), side_maps()):
        (output / f'{name}.png').write_bytes(data)
    for name, data in zip(('hood-shoulder-albedo', 'hood-shoulder-roughness-coat'), top_maps()):
        (output / f'{name}.png').write_bytes(data)
    for name, data in zip(('flare-albedo', 'flare-roughness', 'flare-normal'), flare_maps()):
        (output / f'{name}.png').write_bytes(data)
    for domain, generate in (('front', front_maps), ('rear', rear_maps)):
        for role, data in zip(('albedo', 'roughness-coat', 'normal'), generate()):
            (output / f'{domain}-fascia-{role}.png').write_bytes(data)
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
