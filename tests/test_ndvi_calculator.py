"""
Testes básicos para o NDVI Calculator.
"""

import numpy as np
import pytest

from src.processing.ndvi_calculator import NDVICalculator


class TestNDVICalculator:
    """Testes para a calculadora de NDVI."""

    def test_calculate_ndvi_basic(self):
        """Testa cálculo básico de NDVI."""
        nir = np.array([[800, 850], [900, 820]])
        red = np.array([[100, 120], [110, 105]])

        ndvi = NDVICalculator.calculate_ndvi(nir, red)

        # Verificar forma
        assert ndvi.shape == (2, 2)

        # Verificar valores no intervalo correto
        assert np.all(ndvi >= -1.0) and np.all(ndvi <= 1.0)

        # Verificar cálculo manual para primeiro pixel
        expected_first = (800 - 100) / (800 + 100)
        np.testing.assert_almost_equal(ndvi[0, 0], expected_first, decimal=5)

    def test_calculate_ndvi_with_mask(self):
        """Testa NDVI com máscara."""
        nir = np.array([[800, 850], [900, 820]])
        red = np.array([[100, 120], [110, 105]])
        mask = np.array([[True, False], [True, True]])

        ndvi = NDVICalculator.calculate_ndvi(nir, red, mask)

        # Pixel mascarado deve ser NaN
        assert np.isnan(ndvi[0, 1])

        # Pixels não mascarados devem ter valores válidos
        assert not np.isnan(ndvi[0, 0])
        assert not np.isnan(ndvi[1, 0])

    def test_calculate_ndvi_zero_division(self):
        """Testa tratamento de divisão por zero."""
        nir = np.array([[0, 100], [200, 0]])
        red = np.array([[0, 50], [50, 0]])

        ndvi = NDVICalculator.calculate_ndvi(nir, red)

        # Onde nir + red = 0, deve ser NaN
        assert np.isnan(ndvi[0, 0])
        assert np.isnan(ndvi[1, 1])

        # Outros valores devem ser válidos
        assert not np.isnan(ndvi[0, 1])
        assert not np.isnan(ndvi[1, 0])

    def test_classify_ndvi(self):
        """Testa classificação de NDVI."""
        ndvi = np.array([[-0.5, 0.1, 0.3, 0.5, 0.8]])

        classified = NDVICalculator.classify_ndvi(ndvi)

        # Verificar classes
        assert classified[0, 0] == 0  # water
        assert classified[0, 1] == 1  # bare_soil
        assert classified[0, 2] == 2  # sparse_vegetation
        assert classified[0, 3] == 3  # moderate_vegetation
        assert classified[0, 4] == 4  # dense_vegetation

    def test_calculate_statistics(self):
        """Testa cálculo de estatísticas."""
        ndvi = np.array([[0.2, 0.4], [0.6, 0.8]])

        stats = NDVICalculator.calculate_statistics(ndvi)

        # Verificar chaves
        assert "mean" in stats
        assert "median" in stats
        assert "std" in stats
        assert "min" in stats
        assert "max" in stats
        assert "valid_pixels" in stats

        # Verificar valores
        assert stats["mean"] == 0.5
        assert stats["median"] == 0.5
        assert stats["min"] == 0.2
        assert stats["max"] == 0.8
        assert stats["valid_pixels"] == 4

    def test_calculate_statistics_with_nan(self):
        """Testa estatísticas com valores NaN."""
        ndvi = np.array([[0.2, np.nan], [0.6, 0.8]])

        stats = NDVICalculator.calculate_statistics(ndvi)

        # Deve ignorar NaN
        assert stats["valid_pixels"] == 3
        assert stats["total_pixels"] == 4
        np.testing.assert_almost_equal(
            stats["mean"], (0.2 + 0.6 + 0.8) / 3, decimal=5)
