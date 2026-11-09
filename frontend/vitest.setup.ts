// Test-only configuration.
// Async waits (findBy*, waitFor) use Testing Library's default budget of 1000 ms, kept
// explicit here and well below the 5000 ms per-test timeout in vite.config.ts. A stuck wait
// therefore fails with its own message instead of exhausting the whole test.
//
// History: a2d8f26 raised this budget to 5000 ms (equal to the test timeout) to cure an
// intermittent LabelView failure. The real cause was a race in the tests: Search was
// clicked before LabelView enabled it, the click was dropped, and only a later test's
// render let the wait finish. The tests now wait for Search to be enabled and scope their
// queries to their own container, so the larger budget is no longer needed.
import { configure } from "@testing-library/react";

configure({ asyncUtilTimeout: 1000 });
