# LLM-TradeBot Testing Guide (Beginner-Friendly)

## 1. Remember These Three Rules

1. Always run test mode first, never go live directly.
2. After every code change, run automated tests before starting the bot.
3. Passing tests does not guarantee profits, only that "the code is not obviously broken".

## 2. One-Click Test (Recommended)

Run from the project root:

```bash
python3 scripts/run_tests.py
```

Expected output:

```text
82 passed, 1 skipped
```

Explanation:

- `passed` is the number of tests that passed.
- `skipped` is the number of skipped tests (usually because the Dashboard service is not running locally).

## 3. Test a Single Module (Faster)

```bash
python3 scripts/run_tests.py -q tests/test_agent_config.py
```

## 4. Run a Safe Smoke Test (No Live Trading)

```bash
python3 main.py --test --headless --mode once
```

If the return code is `0` and there are no `Traceback` entries in the logs, the main flow is basically runnable.

## 5. Common Failures and Solutions

### Case A: `Connection refused` (localhost:8000)

Cause: Some tests depend on a local web service that is not running.

Solution:

1. This is normal; the test will auto-skip and won't affect the main test results.
2. If you want to verify UI endpoints, start the service separately and re-run.

### Case B: `ModuleNotFoundError` or dependency errors

Solution:

```bash
pip install -r requirements.txt
pip install pytest
```

Then re-run:

```bash
python3 scripts/run_tests.py
```

### Case C: Tests pass but runtime warnings appear

It is recommended to record the warnings first, then clean them up gradually; prioritize warnings that could cause order errors, risk control failures, or process crashes.

## 6. Daily Routine You Can Follow

1. `python3 scripts/run_tests.py`
2. `python3 main.py --test --headless --mode once`
3. Check logs for anomalies, then decide whether to continue with extended test mode
