"""Phone scanner navigation queue: actual Flet bottom buttons, bounded clicks.

Mock the native worker scheduler only; all page selections run the real app's
render_page()/select(). No provider requests, tokens, orders or fake market data.
"""
import unittest
from test_audit import start,event


class ScannerNavigationRecoveryTests(unittest.TestCase):
    def test_scanner_deep_report_does_not_drop_last_bottom_tab(self):
        page,ui=start({"scanner_live":False,"source":"Dhan"})
        ui["select"](3)
        scanner=ui["scan_result"]
        original=list(scanner.controls)
        class Scheduled:
            def __init__(self):self.queued=[]
            def __call__(self,fn,*a):
                self.queued.append((fn,a))
        schedule=Scheduled()
        page.run_thread=schedule
        buttons=[box.content for box in ui["navbar"].controls]
        try:
            # Simulate taps made while an expensive Scanner rebuild is still
            # queued, rather than running a blocking select() per button.
            for index in (0,2,4,5):
                buttons[index].on_click(event(buttons[index]))
            self.assertEqual(ui["current"][0],3)
            self.assertEqual(len(schedule.queued),1)
            self.assertEqual(ui["nav_destination"][0],5)
            while schedule.queued:
                fn,args=schedule.queued.pop(0)
                fn(*args)
            self.assertEqual(ui["current"][0],5)
            self.assertFalse(ui["nav_draining"][0])
            self.assertIsNone(ui["nav_destination"][0])
            # Bottom controls retain identity and can be tapped again.
            buttons[0].on_click(event(buttons[0]))
            self.assertEqual(len(schedule.queued),1)
            fn,args=schedule.queued.pop(0);fn(*args)
            self.assertEqual(ui["current"][0],0)
            self.assertEqual(
                [id(box.content) for box in ui["navbar"].controls],
                [id(button) for button in buttons])
        finally:
            scanner.controls=original

    def test_navigation_worker_exception_clears_busy_and_recovers_later_tap(self):
        page,ui=start({"scanner_live":False,"source":"Dhan"})
        ui["select"](3)
        jobs=[]
        page.run_thread=lambda fn,*a:jobs.append((fn,a))
        old_builder=ui["pages"][1]
        ui["pages"][1]=lambda: (_ for _ in ()).throw(RuntimeError("broken destination"))
        buttons=[box.content for box in ui["navbar"].controls]
        buttons[1].on_click(event(buttons[1]))
        fn,args=jobs.pop(0);fn(*args)
        self.assertEqual(ui["current"][0],3)
        self.assertFalse(ui["nav_draining"][0])
        ui["pages"][1]=old_builder
        buttons[2].on_click(event(buttons[2]))
        fn,args=jobs.pop(0);fn(*args)
        self.assertEqual(ui["current"][0],2)

    def test_offline_harness_keeps_synchronous_navigation(self):
        _,ui=start({"scanner_live":False})
        buttons=[box.content for box in ui["navbar"].controls]
        for idx in (3,4,1,2,0):
            buttons[idx].on_click(event(buttons[idx]))
            self.assertEqual(ui["current"][0],idx)


if __name__=="__main__":unittest.main()
