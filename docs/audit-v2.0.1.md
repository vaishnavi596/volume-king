# BOT KING 2.0.1 mobile audit fixes

The November 4 screenshots showed settings/cache PermissionError, partial refresh status, a short Bot instrument list, and clipped labels. This update uses FLET_APP_STORAGE_DATA for durable app-private files, keeps async native preference writes, and avoids writing preferences on every scroll event.

Home, Scanner, Options and Bot share the configured 50-company selection universe plus indices and custom symbols. Search filters the selectors without removing their stored values. Changing the Bot instrument clears stale strike, premium, lot size and manual confirmation. Calculator results explicitly identify unverified manual examples and show lots × units.

The scanner publishes completed-candle results before fetching news, bounds request waits, recovers from scheduler exceptions, and checks refresh deadlines once per second. Source changes and resume clear the old deadline. Combined analysis distinguishes candle results from pending news and unavailable options. Chart failure text only claims a saved chart when saved candles were loaded. Ranking failures identify individual symbols and provide Retry.

Field help sits beside native field labels. Long switch/checkbox labels wrap separately, agreement shows its actual percentage, Options columns are horizontally scrollable, and settings history uses IST. Yahoo percent change prefers the previous session close over the start of a historical range.

Validation: compile all Python files; run the complete offline Flet regression suite, including app-private storage/restart, all stock selectors, custom symbol persistence, contract reset, quantity calculation, bilingual wrapping, scroll writes, news failures and scheduler deadlines. These tests do not certify phone rendering or current external feed availability.

Broker orders, always-on server execution, notification delivery and backtest reports remain unconnected. Only EMA has a plotted chart overlay. This is a paper build; the Oracle server is not changed by this update. Verify APK behavior on the user's phone before treating any previously observed phone issue as resolved there.
