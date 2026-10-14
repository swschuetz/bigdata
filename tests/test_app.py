"""Regression checks for stale analytics and queue-delay messaging."""

import unittest
from pathlib import Path

from streamlit.testing.v1 import AppTest
from simulation import Cohort


class AnalyticsStatusTests(unittest.TestCase):
    def make_snapshot(self, backlog=5000, congestion=False):
        app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / 'app.py'), default_timeout=30).run()
        app.radio(key='stream_status').set_value('Paused').run()
        app.slider(key='capacity').set_value(100).run()
        sim = app.session_state['simulation_v3']
        sim.total, sim.processed = backlog + 300, 300
        sim.queue.clear()
        if backlog:
            sim.queue.append(Cohort(backlog, 0))
        sim.rows.clear()
        sim.rows.extend({'Cars': 60 if congestion else 20,
                         'Speed (mph)': 10.0 if congestion else 55.0} for _ in range(300))
        app.run()
        self.assertFalse(app.exception)
        return app

    def test_backlog_replaces_healthy_status_and_shows_estimate(self):
        app = self.make_snapshot()
        self.assertIn('Analytics delayed', app.warning[0].value)
        self.assertEqual(len(app.success), 0)
        self.assertIn('New-reading wait: paused', [c.value for c in app.caption])
        app.radio(key='stream_status').set_value('Running').run()
        self.assertIn('New-reading wait: ≈50 s', [c.value for c in app.caption])
        self.assertEqual(len(app.success), 0)
        app.button[0].click().run()
        self.assertIn('New-reading wait: ≈9 s', [c.value for c in app.caption])
        self.assertFalse(app.exception)

    def test_delayed_congestion_finding_remains_visible(self):
        app = self.make_snapshot(congestion=True)
        self.assertIn('Analytics delayed', app.warning[0].value)
        self.assertIn('Congestion detected in the processed readings.', [c.value for c in app.caption])
        self.assertEqual(len(app.success), 0)

    def test_paused_snapshot_is_not_reported_as_live(self):
        app = self.make_snapshot(backlog=0, congestion=True)
        self.assertIn('Analytics paused', app.info[0].value)
        self.assertIn('Congestion detected in the last processed readings.', [c.value for c in app.caption])
        self.assertEqual(len(app.success), 0)

    def test_clear_queue_restores_current_status_and_reset_clears_wait(self):
        app = self.make_snapshot(backlog=0)
        app.radio(key='stream_status').set_value('Running').run()
        self.assertIn('Traffic flowing', app.success[0].value)
        self.assertIn('New-reading wait: ≈0 s', [c.value for c in app.caption])
        app.button[2].click().run()
        self.assertIn('Waiting for processed sensor readings', app.info[0].value)
        self.assertIn('New-reading wait: ≈0 s', [c.value for c in app.caption])
        self.assertFalse(app.exception)


if __name__ == '__main__':
    unittest.main()
