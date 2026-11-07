import numpy as np
import pytest

from conftest import ROOT
from bake import bake, read_bin, write_bin

REF = str(ROOT / "tools" / "axolotl-reference.jpg")


@pytest.fixture(scope="module")
def data():
    return bake(REF)


def test_roundtrip(data, tmp_path):
    out = tmp_path / "a.bin"
    write_bin(str(out), data)
    back = read_bin(str(out))
    for key in ("col", "geo", "kind", "part", "grow"):
        assert np.array_equal(back[key], data[key]), key
    assert np.allclose(back["pos"], data["pos"], atol=1e-3)


def test_kind_proportions(data):
    k = data["kind"]
    n = len(k)
    assert 40 <= (k == 2).sum() <= 400
    assert 0.15 <= (k == 1).sum() / n <= 0.35
    assert (k == 3).sum() / n >= 0.05


def test_four_legs(data):
    part, kind, pos = data["part"], data["kind"], data["pos"]
    for p in (1, 2, 3, 4):
        assert (part == p).sum() >= 150, p
    assert np.all(kind[part > 0] == 3)
    mx = {p: pos[part == p, 0].mean() for p in (1, 2, 3, 4)}
    my = {p: pos[part == p, 1].mean() for p in (1, 2, 3, 4)}
    assert mx[1] < 0 and mx[3] < 0
    assert mx[2] > 0 and mx[4] > 0
    assert my[1] > my[3]


def test_grow_runs_outward(data):
    grow, kind, part, pos = data["grow"], data["kind"], data["part"], data["pos"]
    assert np.all(grow[kind != 3] == 0)
    leg = part == 1
    far = np.abs(pos[leg & (grow > 200), 0]).mean()
    near = np.abs(pos[leg & (grow < 50), 0]).mean()
    assert far > near


def test_extent(data):
    y = data["pos"][:, 1]
    assert 9.0 <= y.max() - y.min() <= 10.0
    assert np.abs(data["pos"][:, 2]).max() <= 1.3


def test_file_size(data, tmp_path):
    out = tmp_path / "a.bin"
    write_bin(str(out), data)
    assert out.stat().st_size <= 450_000
