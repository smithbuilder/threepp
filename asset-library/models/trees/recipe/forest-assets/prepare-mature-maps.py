import os
from pathlib import Path
from PIL import Image
recipeDir=Path(__file__).resolve().parent; root=Path(os.environ['THREEPP_FOREST_SOURCE_DIR'])
for path in (root/'fir_tree_01').glob('*.png'):
    if path.stem.endswith('_8bit'):continue
    Image.open(path).convert('L' if path.stem.endswith(('_alpha','_rough')) else 'RGB').save(path.with_stem(path.stem+'_8bit'),optimize=True)
colour=Image.open(root/'fir_tree_01'/'twig_diff_8bit.png').convert('RGBA');colour.putalpha(Image.open(root/'fir_tree_01'/'twig_alpha_8bit.png').convert('L'));colour.save(root/'fir_tree_01'/'twig_basecolor_8bit.png',optimize=True)
