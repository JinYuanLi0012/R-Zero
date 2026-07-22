#!/usr/bin/env python3

from __future__ import annotations

import math
import unittest

import numpy as np

from methods.task_vector_rzero.analysis.geometry import (
    cosine_from_gram,
    derive_geometry,
    uncentered_coordinates,
)


class GeometryTest(unittest.TestCase):
    def setUp(self) -> None:
        e1 = np.array([1.0, 0.0, 0.0, 0.0])
        e2 = np.array([0.0, 1.0, 0.0, 0.0])
        e3 = np.array([0.0, 0.0, 1.0, 0.0])
        e4 = np.array([0.0, 0.0, 0.0, 1.0])
        questioner = [e1, e2, -e1, e1 + e2, e3]
        rank1 = [2 * e1, e2, e3, e4, e1 - e2]
        full = [4 * e1, 2 * e2, e3, 2 * e4, 2 * (e1 - e2)]
        self.vectors = np.stack(questioner + rank1 + full)
        self.gram = self.vectors @ self.vectors.T
        self.ids = (
            [f"questioner_full_r{i}" for i in range(1, 6)]
            + [f"solver_rank1_r{i}" for i in range(1, 6)]
            + [f"solver_full_r{i}" for i in range(1, 6)]
        )

    def test_cosine_known_directions(self) -> None:
        cosine = cosine_from_gram(self.gram)
        self.assertAlmostEqual(cosine[0, 1], 0.0)
        self.assertAlmostEqual(cosine[0, 2], -1.0)
        self.assertAlmostEqual(cosine[5, 10], 1.0)
        np.testing.assert_allclose(np.diag(cosine), np.ones(15))

    def test_history_and_relex_metrics(self) -> None:
        derived = derive_geometry(self.gram, self.ids)
        questioner_history = derived["historical"]["questioner_full"]
        self.assertAlmostEqual(questioner_history[1]["history_cosine"], 0.0)
        self.assertAlmostEqual(questioner_history[2]["history_cosine"], -1 / math.sqrt(2))
        relex = derived["relex"]
        self.assertAlmostEqual(relex[0]["norm_ratio"], 0.5)
        self.assertAlmostEqual(relex[0]["cosine"], 1.0)
        self.assertAlmostEqual(relex[0]["relative_reconstruction_error"], 0.5)
        self.assertAlmostEqual(relex[2]["norm_ratio"], 1.0)
        self.assertAlmostEqual(relex[2]["relative_reconstruction_error"], 0.0)

    def test_uncentered_coordinates_are_deterministic(self) -> None:
        coordinates_a, explained_a = uncentered_coordinates(self.gram, dimensions=2)
        coordinates_b, explained_b = uncentered_coordinates(self.gram, dimensions=2)
        np.testing.assert_allclose(coordinates_a, coordinates_b)
        np.testing.assert_allclose(explained_a, explained_b)
        self.assertEqual(coordinates_a.shape, (15, 2))
        self.assertTrue(np.all(explained_a >= 0))
        self.assertLessEqual(float(explained_a.sum()), 1.0 + 1e-12)

    def test_trajectory_contains_base_and_two_families(self) -> None:
        trajectory = derive_geometry(self.gram, self.ids)["trajectory"]
        self.assertEqual(
            trajectory["labels"],
            ["Base", "Q1", "Q2", "Q3", "Q4", "Q5", "V1", "V2", "V3", "V4", "V5"],
        )
        np.testing.assert_allclose(trajectory["coordinates"][0], np.zeros(2), atol=1e-12)
        np.testing.assert_allclose(trajectory["gram"][0], np.zeros(11), atol=1e-12)


if __name__ == "__main__":
    unittest.main()
