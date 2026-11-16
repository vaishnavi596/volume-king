"""Offline Flet control identity test for BOT KING changed-data-only Watchlist."""
import asyncio
import time
import unittest
from unittest.mock import patch
from test_audit import start


class WatchlistMountedCellBehavior(unittest.TestCase):
    def test_price_change_updates_same_mounted_row_without_page_navigation(self):
        page,v=start({"source":"Dhan","scanner_live":False,"last_page":2})
        v["select"](4)
        symbols=list(v["watch_row_cells"])
        self.assertTrue(symbols,"Expected at least one saved watchlist row")
        sym=symbols[0]
        before_row=v["watch_list"].controls[0]
        cells=v["watch_row_cells"][sym]
        original_price=cells[0]
        before_cell_ids=tuple(map(id,cells))
        original_page_controls=v["body"].controls
        v["quotes"][sym]={"source":"Dhan","price":2077.3,"change":2.5,
                           "fetched_at":time.time(),"freshness":"unverified",
                           "live_verified":False}
        v["app_active"][0]=True
        iterations=[0]
        async def once_then_cancel(_seconds):
            iterations[0]+=1
            if iterations[0]>1:raise asyncio.CancelledError()
        with patch("asyncio.sleep",side_effect=once_then_cancel):
            with self.assertRaises(asyncio.CancelledError):
                asyncio.run(v["watch_visible_tick"]())
        self.assertEqual(cells[0].value,"2,077.30")
        self.assertEqual(cells[1].value,"+2.50%")
        self.assertIs(v["watch_list"].controls[0],before_row)
        self.assertIs(v["watch_row_cells"][sym][0],original_price)
        self.assertEqual(tuple(map(id,v["watch_row_cells"][sym])),before_cell_ids)
        self.assertIs(v["body"].controls,original_page_controls)
        # Local price change must not enqueue a new broker request.
        self.assertFalse(any(getattr(fn,"__name__","")=="refresh_watch_batch"
                             for fn,args in page.tasks))
