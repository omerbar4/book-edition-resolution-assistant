// Test-only configuration (post-evaluation delivery fix, 2026-11-08).
// Testing Library's default async timeout is 1000 ms. Under CPU load, the LabelView
// "is blind-first" test intermittently waited longer than that for mocked search results
// to render (reproduced: 1 failure in 25 runs with 10 busy CPU loops). Raising the timeout
// changes no assertion and no application code.
import { configure } from "@testing-library/react";

configure({ asyncUtilTimeout: 5000 });
