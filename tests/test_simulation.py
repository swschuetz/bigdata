import unittest

from simulation import MAX_COHORTS, MAX_ROWS, Simulation


class SimulationTests(unittest.TestCase):
    def advance(self, sim, now, **changes):
        controls = dict(rate=sim.rate, capacity=sim.capacity, jam=sim.jam, running=sim.running)
        controls.update(changes)
        sim.advance(now, **controls)
        self.assertEqual(sim.total, sim.processed + sim.backlog)
        self.assertEqual(sim.backlog, sum(c.count for c in sim.queue))
        self.assertTrue(all(0 <= c.jam_count <= c.count for c in sim.queue))

    def test_overload_and_scaling_drain_queue(self):
        sim = Simulation(0, rate=1000, capacity=300, seed=1)
        self.advance(sim, 1)
        self.assertEqual((sim.total, sim.processed, sim.backlog), (1000, 300, 700))
        self.advance(sim, 1, capacity=1500)
        self.advance(sim, 2)
        self.assertEqual(sim.backlog, 200)
        self.advance(sim, 3)
        self.assertEqual(sim.backlog, 0)
        self.assertEqual(sim.processing_rate, 1000)

    def test_control_changes_do_not_apply_retroactively(self):
        sim = Simulation(0, rate=10, capacity=100, seed=1)
        self.advance(sim, 1, rate=1000, capacity=1500, jam=True)
        self.assertEqual(sim.total, 10)
        self.assertTrue(all(row['Speed (mph)'] >= 42 for row in sim.rows))
        self.advance(sim, 2)
        self.assertEqual(sim.total, 1010)
        self.assertTrue(sim.analytics()['congestion'])

    def test_pause_freezes_both_sides_and_resume_continues(self):
        sim = Simulation(0, rate=1000, capacity=100, seed=1)
        self.advance(sim, 1, running=False)
        snapshot = (sim.total, sim.processed, sim.backlog, list(sim.rows), sim.active_seconds)
        self.advance(sim, 101, capacity=1500, jam=True)
        self.assertEqual(snapshot, (sim.total, sim.processed, sim.backlog, list(sim.rows), sim.active_seconds))
        self.assertEqual((sim.incoming_rate, sim.processing_rate), (0, 0))
        self.advance(sim, 101, running=True)
        self.advance(sim, 102)
        self.assertEqual(sim.total, 2000)
        self.assertLess(sim.backlog, 900)

    def test_incident_detected_and_cleared_from_processed_data(self):
        sim = Simulation(0, seed=1)
        self.advance(sim, 1, jam=True)
        self.assertFalse(sim.analytics()['congestion'])
        self.advance(sim, 2)
        self.assertTrue(sim.analytics()['congestion'])
        self.assertLess(sim.analytics()['speed'], 40)
        self.advance(sim, 2, jam=False)
        self.advance(sim, 4)
        self.assertFalse(sim.analytics()['congestion'])
        self.assertEqual(sim.analytics()['slow_share'], 0)

    def test_backlog_delays_incident_detection(self):
        sim = Simulation(0, rate=1000, capacity=100, seed=1)
        self.advance(sim, 1, jam=True)
        for second in range(2, 11):
            self.advance(sim, second)
            self.assertFalse(sim.analytics()['congestion'])
        self.advance(sim, 11)
        self.assertFalse(sim.analytics()['congestion'])
        self.advance(sim, 12)
        self.assertTrue(sim.analytics()['congestion'])

    def test_long_run_keeps_history_samples_and_queue_bounded(self):
        sim = Simulation(0, rate=1000, capacity=100, seed=1)
        for tick in range(1, 1001):
            self.advance(sim, tick / 2, jam=bool(tick % 2))
        self.assertEqual(sim.total, 500000)
        self.assertEqual(sim.processed, 50000)
        self.assertEqual(len(sim.rows), MAX_ROWS)
        self.assertLessEqual(len(sim.queue), MAX_COHORTS)
        self.assertLessEqual(len(sim.history), 600)
        self.assertLessEqual(sim.history[0]['Seconds'], 440)
        self.assertGreaterEqual(sim.history[1]['Seconds'], 440)

    def test_fractional_arrivals_and_idle_capacity(self):
        sim = Simulation(0, rate=10, capacity=1500, seed=1)
        for tick in range(1, 401):
            self.advance(sim, tick / 32)
        self.assertEqual((sim.total, sim.processed, sim.backlog), (125, 125, 0))
        self.advance(sim, 12.5, rate=1000, capacity=100)
        self.advance(sim, 13.5)
        self.assertEqual(sim.backlog, 900)  # Idle spare capacity cannot be banked.

    def test_empty_state_and_fresh_reset(self):
        sim = Simulation(0)
        self.assertIsNone(sim.analytics())
        self.assertEqual((sim.total, sim.processed, sim.backlog), (0, 0, 0))


if __name__ == '__main__':
    unittest.main()
