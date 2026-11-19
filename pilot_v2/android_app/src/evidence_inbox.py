"""V2 app-owned offline evidence entry point, NOT a network/auth client.

Only a future authenticated transport adapter may assert trusted_transport=True.
Each lane retains independent source revisions and historical-only presentation.
"""
from candle_history import LocalCandleHistory
from filter_evidence import LocalFilterEvidence
from option_evidence import LocalOptionEvidence, LocalExpiryChoices, OptionEvidenceError
from candle_filter_gate import accept_candle_trend
from candle_option_views import LocalOptionStrikes
from listed_atm_adapter import normalized_atm_window
from option_filter_gate import (
    accept_option_factors, accept_option_metrics, accept_expiry_roster,
    select_option_expiry,
)

INDEXES = ("NIFTY", "BANKNIFTY", "SENSEX")


class DeviceEvidenceInbox:
    """One V2 UI-owned candle/option/five-filter state; never a signal producer."""

    def __init__(self):
        self.candles = LocalCandleHistory()
        self.filters = LocalFilterEvidence()
        self.options = LocalOptionEvidence()
        self.expiries = LocalExpiryChoices()
        self.strikes = LocalOptionStrikes()  # Validated, never synthesized CE/PE.

    @staticmethod
    def allowed(selected_equities):
        equities = tuple(selected_equities)
        if (len(equities) > 70
                or any(type(symbol) is not str or not symbol
                       or symbol in INDEXES for symbol in equities)
                or len(equities) != len(set(equities))):
            raise ValueError("Invalid app-owned equity roster")
        return INDEXES + equities

    def apply_candles(self, symbol, timeframe, revision, bars, *,
                      selected_equities=(), trusted_transport=False):
        if trusted_transport is not True:
            raise ValueError("Authenticated candle transport required")
        return self.candles.accept(
            symbol, timeframe, revision, bars,
            allowed_symbols=self.allowed(selected_equities))

    def apply_candle_trend(self, symbol, timeframe, revision, evidence, *,
                           selected_equities=(), trusted_transport=False):
        self.allowed(selected_equities)
        return accept_candle_trend(
            self.candles, self.filters, symbol, timeframe, revision, evidence,
            selected_equities=selected_equities,
            trusted_transport=trusted_transport)

    def apply_expiries(self, symbol, revision, available, *,
                       selected_equities=(), trusted_transport=False):
        allowed = self.allowed(selected_equities)
        return accept_expiry_roster(
            self.filters, self.expiries, symbol, revision, available,
            allowed_symbols=allowed, selected_equities=selected_equities,
            trusted_transport=trusted_transport)

    def select_expiry(self, symbol, expiry, *, selected_equities=()):
        self.allowed(selected_equities)
        return select_option_expiry(
            self.filters, self.expiries, symbol, expiry,
            selected_equities=selected_equities)

    def apply_options(self, payload, *, selected_equities=(),
                      trusted_transport=False):
        self.allowed(selected_equities)
        return accept_option_metrics(
            self.filters, self.options, self.expiries, payload,
            selected_equities=selected_equities,
            trusted_transport=trusted_transport)

    def apply_option_strikes(self, payload, *, selected_equities=(),
                             trusted_transport=False):
        self.allowed(selected_equities)
        return self.strikes.accept(
            payload, self.expiries, selected_equities=selected_equities,
            trusted_transport=trusted_transport)

    def apply_listed_option_window(self, *, symbol, expiry, revision, observed_at,
                                   spot, listed_rows, selected_equities=(),
                                   trusted_transport=False):
        """Normalize a trusted full listed Dhan chain before publishing ATM±3.

        Caller must have verified transport identity, same-source underlying spot,
        expiry and listed strike observation. No network work occurs here.
        """
        self.allowed(selected_equities)
        if trusted_transport is not True:
            raise OptionEvidenceError("Authenticated Dhan option evidence required")
        if self.expiries.selected(
                symbol, selected_equities=selected_equities) != expiry:
            raise OptionEvidenceError("Only the selected verified expiry is eligible")
        payload = normalized_atm_window(
            symbol=symbol, expiry=expiry, revision=revision,
            observed_at=observed_at, spot=spot, listed_rows=listed_rows,
            trusted_transport=True)
        return self.apply_option_strikes(
            payload, selected_equities=selected_equities,
            trusted_transport=True)

    def apply_option_factors(self, symbol, timeframe, revision, evidence, *,
                             selected_equities=(), trusted_transport=False):
        self.allowed(selected_equities)
        return accept_option_factors(
            self.filters, self.options, self.expiries, symbol, timeframe,
            revision, evidence, selected_equities=selected_equities,
            trusted_transport=trusted_transport)

    def forget_removed(self, selected_equities):
        self.allowed(selected_equities)
        self.candles.forget_removed(selected_equities)
        self.filters.forget_removed(selected_equities)
        self.options.forget_removed(selected_equities)
        self.expiries.forget_removed(selected_equities)
        self.strikes.forget_removed(selected_equities)
