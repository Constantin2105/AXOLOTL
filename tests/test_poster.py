import numpy as np
import pytest
from PIL import Image

from conftest import ROOT
from bake import read_bin
from poster import render_poster


@pytest.fixture(scope="module")
def poster(tmp_path_factory):
    out = tmp_path_factory.mktemp("poster") / "p.webp"
    render_poster(read_bin(str(ROOT / "assets" / "axolotl.v1.bin")), str(out))
    return out


def test_poster_file(poster):
    assert poster.stat().st_size <= 150_000
    assert Image.open(poster).mode == "RGBA"


def test_poster_coverage(poster):
    alpha = np.asarray(Image.open(poster))[..., 3]
    share = (alpha > 20).mean()
    assert 0.08 <= share <= 0.5
