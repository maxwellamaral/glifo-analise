"""
Testes das funções puras de bitmap em analysis/bitmap.py.

História de usuário:
    Como engenheiro de hardware tátil, quero que as funções de
    análise de bitmap produzam métricas psicofísicas numericamente
    corretas para que a triagem de glifos seja reproduzível e
    auditável independente do ambiente.
"""
import numpy as np
import pytest

from glifo_analise.config import FONT_PATH
from glifo_analise.analysis.bitmap import (
    _render_bitmap,
    _pixel_density,
    _edge_complexity,
    _iou,
    _effective_resolution,
    _collect_mapped_codepoints,
    _build_profiles,
)


class TestPixelDensity:
    def test_all_ones_returns_1(self):
        bm = np.ones((8, 8), dtype=np.uint8)
        assert _pixel_density(bm) == pytest.approx(1.0)

    def test_all_zeros_returns_0(self):
        bm = np.zeros((8, 8), dtype=np.uint8)
        assert _pixel_density(bm) == pytest.approx(0.0)

    def test_half_filled(self):
        bm = np.zeros((4, 4), dtype=np.uint8)
        bm[0:2, :] = 1
        assert _pixel_density(bm) == pytest.approx(0.5)


class TestEdgeComplexity:
    def test_solid_block_has_no_internal_edges(self):
        bm = np.ones((6, 6), dtype=np.uint8)
        assert _edge_complexity(bm) == pytest.approx(0.0)

    def test_empty_block_has_no_edges(self):
        bm = np.zeros((6, 6), dtype=np.uint8)
        assert _edge_complexity(bm) == pytest.approx(0.0)

    def test_checkerboard_has_high_complexity(self):
        bm = np.zeros((6, 6), dtype=np.uint8)
        bm[::2, ::2] = 1
        bm[1::2, 1::2] = 1
        assert _edge_complexity(bm) > 0.0

    def test_single_isolated_pixel_has_edges(self):
        # Um pixel isolado no centro produz contraste com os 4 vizinhos via np.roll
        # → contribui como pixel de borda; edge/total = 5/25 = 0.20
        bm = np.zeros((5, 5), dtype=np.uint8)
        bm[2, 2] = 1
        assert _edge_complexity(bm) == pytest.approx(0.20)


class TestIoU:
    def test_identical_bitmaps_return_1(self):
        bm = np.zeros((8, 8), dtype=np.uint8)
        bm[2:6, 2:6] = 1
        assert _iou(bm, bm) == pytest.approx(1.0)

    def test_disjoint_bitmaps_return_0(self):
        ref = np.zeros((8, 8), dtype=np.uint8)
        ref[0:4, 0:4] = 1
        tst = np.zeros((8, 8), dtype=np.uint8)
        tst[4:8, 4:8] = 1
        assert _iou(ref, tst) == pytest.approx(0.0)

    def test_partial_overlap(self):
        ref = np.zeros((4, 4), dtype=np.uint8)
        ref[:, :2] = 1      # metade esquerda
        tst = np.zeros((4, 4), dtype=np.uint8)
        tst[:, 1:3] = 1     # colunas 1-2 (sobreposição de coluna 1)
        val = _iou(ref, tst)
        # intersec = 4, union = 12 → 1/3
        assert 0.0 < val < 1.0


class TestRenderBitmap:
    def test_returns_correct_shape(self, profiles):
        from glifo_analise.config import FONT_PATH
        from PIL import ImageFont
        font = ImageFont.truetype(str(FONT_PATH), 11)
        resolution = (13, 13)
        bm = _render_bitmap("A", font, resolution)
        assert bm.shape == (13, 13)

    def test_values_are_0_or_1(self, profiles):
        from PIL import ImageFont
        font = ImageFont.truetype(str(FONT_PATH), 11)
        bm = _render_bitmap("A", font, (10, 10))
        assert set(np.unique(bm)).issubset({0, 1})

    def test_dtype_is_uint8(self, profiles):
        from PIL import ImageFont
        font = ImageFont.truetype(str(FONT_PATH), 11)
        bm = _render_bitmap("a", font, (8, 8))
        assert bm.dtype == np.uint8


class TestEffectiveResolution:
    def test_effective_le_declared(self, profiles):
        res = (13, 13)
        (eff_w, eff_h), _ = _effective_resolution(profiles, res)
        assert eff_w <= 13
        assert eff_h <= 13

    def test_effective_positive(self, profiles):
        (eff_w, eff_h), _ = _effective_resolution(profiles, (10, 10))
        assert eff_w > 0
        assert eff_h > 0

    def test_crop_box_indices_valid(self, profiles):
        res = (13, 13)
        _, (r0, r1, c0, c1) = _effective_resolution(profiles, res)
        assert 0 <= r0 <= r1 < res[1]
        assert 0 <= c0 <= c1 < res[0]

    def test_cache_returns_same_result(self, profiles):
        res = (10, 10)
        result1 = _effective_resolution(profiles, res)
        result2 = _effective_resolution(profiles, res)
        assert result1[0] == result2[0]


class TestCollectAndBuildProfiles:
    def test_codepoints_nonempty(self):
        cps = _collect_mapped_codepoints(FONT_PATH)
        assert len(cps) > 0

    def test_codepoints_are_ints(self):
        cps = _collect_mapped_codepoints(FONT_PATH)
        assert all(isinstance(cp, int) for cp in cps)

    def test_profiles_length_matches_codepoints(self):
        cps = _collect_mapped_codepoints(FONT_PATH)
        profs = _build_profiles(cps, FONT_PATH)
        assert len(profs) == len(cps)

    def test_profile_bitmap_shape(self):
        cps = _collect_mapped_codepoints(FONT_PATH)
        profs = _build_profiles(cps[:5], FONT_PATH)
        for p in profs:
            assert p.bitmap_ref.shape == (64, 64)
