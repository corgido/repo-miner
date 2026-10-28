"""The measures on planted data: a silence and a change of character must cut chapters; nothing else may."""
import random
import unittest

import helpers  # noqa: F401  (puts the package on the path)
from repo_miner import measures as M


class MeasuresTest(unittest.TestCase):
    def test_entropy(self):
        self.assertAlmostEqual(M.entropy([1, 1]), 1.0)
        self.assertEqual(M.entropy([5]), 0.0)
        self.assertEqual(M.entropy([]), 0.0)

    def test_a_silence_always_cuts(self):
        times = [i * 3600 for i in range(40)] + [10 ** 7 + i * 3600 for i in range(40)]
        values = [["a"]] * 80
        segs = M.stratify(times, values, seam_gap=24 * 3600, min_size=6)
        self.assertEqual([(s["a"], s["b"]) for s in segs], [(0, 40), (40, 80)])
        self.assertTrue(all(s["seam"] for s in segs))

    def test_a_change_of_character_cuts_near_where_it_happens(self):
        rng = random.Random(7)
        values = [[rng.choice("ab")] for _ in range(150)] + [[rng.choice("cd")] for _ in range(150)]
        times = [i * 600 for i in range(300)]
        segs = M.stratify(times, values, seam_gap=10 ** 9, min_size=10)
        self.assertEqual(len(segs), 2)
        self.assertLess(abs(segs[0]["b"] - 150), 5)

    def test_noise_does_not_cut(self):
        rng = random.Random(3)
        values = [[rng.choice("abc")] for _ in range(400)]
        segs = M.stratify([i * 600 for i in range(400)], values, seam_gap=10 ** 9, min_size=10)
        self.assertEqual(len(segs), 1)

    def test_stratify_is_deterministic(self):
        rng = random.Random(11)
        values = [[rng.choice("abcd"), rng.choice("xy")] for _ in range(500)]
        times = sorted(rng.randrange(10 ** 8) for _ in range(500))
        self.assertEqual(M.stratify(times, values, 10 ** 6), M.stratify(times, values, 10 ** 6))

    def test_lifts(self):
        rows = M.lifts(["a"] * 10 + ["b"] * 10, ["a"] * 8 + ["b"] * 2, "x")
        self.assertEqual(rows[0]["value"], "a")
        self.assertGreater(rows[0]["lift"], 0.6)

    def test_tokens_skip_identifiers_trailers_and_names(self):
        words = M.tokens("Fix parser\n\nCo-Authored-By: Claude <noreply@anthropic.com>\nsession 3f9a8b7c6d5e4f3a2b1c "
                         "Merge pull request #12 from jane/patch-1 refactor tokenizer", exclude=frozenset({"jane"}))
        self.assertEqual(words, ["parser", "session", "refactor", "tokenizer"])

    def test_poisson_and_concentration(self):
        self.assertEqual(M.poisson_tail_bits(1, 3.0), 0.0)
        self.assertGreater(M.poisson_tail_bits(20, 2.0), 20)
        c = M.concentration([100, 1, 1, 1, 1])
        self.assertEqual(c["k"], 1)
        self.assertGreater(c["gini"], 0.7)


if __name__ == "__main__":
    unittest.main()
