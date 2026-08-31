from __future__ import annotations

import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd

from src.datos.descarga_gdelt import (
    CoberturaGDELT,
    auditar_cobertura_local,
    descargar_rango,
)
from src.datos.etiquetas import aplicar_corte_horario, mascara_historial_gdelt_completo
from src.entrenamiento.evaluacion import ResultadoExperimento, simular_estrategia


class CorteHorarioTests(unittest.TestCase):
    def test_cierre_local_respeta_dst(self) -> None:
        eventos = pd.DataFrame({
            "SQLDATE": ["20240701", "20240701", "20240115", "20240115"],
            "DATEADDED": [
                "20240701195959",
                "20240701200000",
                "20240115205959",
                "20240115210000",
            ],
        })

        salida = aplicar_corte_horario(eventos)

        self.assertEqual(
            salida["fecha_grafo"].dt.strftime("%Y-%m-%d").tolist(),
            ["2024-07-01", "2024-07-02", "2024-01-15", "2024-01-16"],
        )

    def test_excluye_toda_ventana_afectada_por_un_dia_ausente(self) -> None:
        mascara = mascara_historial_gdelt_completo(
            pd.to_datetime(["2025-01-09", "2025-01-10", "2025-03-11", "2025-03-12"]),
            [date(2025, 1, 10)],
            ventana_dias=60,
        )

        self.assertEqual(mascara.tolist(), [True, False, False, True])


class CoberturaTests(unittest.TestCase):
    def test_distingue_archivos_faltantes_y_vacios(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            directorio = Path(tmp)
            (directorio / "20250101.export.CSV").write_text("dato", encoding="utf-8")
            (directorio / "20250102.export.CSV").touch()

            cobertura = auditar_cobertura_local(
                date(2025, 1, 1), date(2025, 1, 3), directorio,
            )

        self.assertFalse(cobertura.completa)
        self.assertEqual(cobertura.vacios, (date(2025, 1, 2),))
        self.assertEqual(cobertura.faltantes, (date(2025, 1, 3),))
        self.assertEqual(len(cobertura.rutas), 1)

    def test_exigir_completo_acepta_ausencia_confirmada_como_404(self) -> None:
        dia = date(2025, 1, 1)
        cobertura = CoberturaGDELT(
            fecha_inicio=dia,
            fecha_fin=dia,
            rutas=(),
            faltantes=(dia,),
            vacios=(),
        )
        with (
            patch("src.datos.descarga_gdelt.descargar_dia", return_value=None),
            patch("src.datos.descarga_gdelt.auditar_cobertura_local", return_value=cobertura),
        ):
            rutas = descargar_rango(dia, dia, exigir_completo=True)

        self.assertEqual(rutas, [])

    def test_exigir_completo_rechaza_hueco_no_confirmado(self) -> None:
        dia = date(2025, 1, 1)
        cobertura = CoberturaGDELT(
            fecha_inicio=dia,
            fecha_fin=dia,
            rutas=(),
            faltantes=(dia,),
            vacios=(),
        )
        with (
            patch("src.datos.descarga_gdelt.descargar_dia", return_value=Path("aparente.csv")),
            patch("src.datos.descarga_gdelt.auditar_cobertura_local", return_value=cobertura),
            self.assertRaises(RuntimeError),
        ):
            descargar_rango(dia, dia, exigir_completo=True)


class EvaluacionOOSTests(unittest.TestCase):
    def test_ensemble_promedia_semillas_sin_duplicar_fechas(self) -> None:
        resultado = ResultadoExperimento()
        fechas = pd.to_datetime(["2025-01-02", "2025-01-03"]).values
        reales = np.array([0, 2])
        retornos = np.array([-0.01, 0.02])
        resultado.agregar_oos(
            0, 0, [10, 11], fechas,
            [[0.6, 0.3, 0.1], [0.1, 0.2, 0.7]], reales, retornos,
        )
        resultado.agregar_oos(
            0, 1, [10, 11], fechas,
            [[0.4, 0.5, 0.1], [0.1, 0.4, 0.5]], reales, retornos,
        )

        tabla = resultado.tabla_oos(promediar_semillas=True)

        self.assertEqual(len(tabla), 2)
        self.assertEqual(tabla["n_semillas"].tolist(), [2, 2])
        np.testing.assert_allclose(tabla["p_baja"].to_numpy(), [0.5, 0.1])
        np.testing.assert_allclose(tabla["p_sube"].to_numpy(), [0.1, 0.6])

    def test_backtest_aplica_coste_solo_al_cambiar_posicion(self) -> None:
        probabilidades = np.array([[0.05, 0.05, 0.90], [0.05, 0.05, 0.90]])
        metricas = simular_estrategia(
            probabilidades,
            np.zeros(2),
            coste_transaccion_bps=10.0,
            coste_short_anual_bps=0.0,
        )

        self.assertEqual(metricas.n_cambios_posicion, 1)
        self.assertAlmostEqual(metricas.coste_transaccion_total, 0.001)
        self.assertAlmostEqual(metricas.rentabilidad_estrategia, -0.001)


if __name__ == "__main__":
    unittest.main()
