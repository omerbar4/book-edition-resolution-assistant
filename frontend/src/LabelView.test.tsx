import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { LabelView } from "./LabelView";

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

const queue = {
  items: [
    {
      draft_id: "dev-001",
      split: "dev",
      query: { title: "Dune", physical_format: "paperback" },
      template: "t",
      labeled: false,
    },
  ],
  reasons: ["underspecified", "out_of_corpus"],
  labeled: 0,
  total: 1,
};
const rows = [
  {
    edition_id: "OL1M",
    work_id: "OL1W",
    title: "Dune",
    subtitle: null,
    authors: ["Frank Herbert"],
    publishers: ["Ace"],
    publish_year: 1990,
    physical_format: "paperback",
    edition_name: null,
    languages: ["eng"],
    isbn_13: [],
    isbn_10: [],
  },
];

const searchPage = {
  total: 120,
  offset: 0,
  limit: 50,
  returned: 1,
  truncated: true,
  match_rule: "m",
  order: "alphabetical",
  items: rows,
};

describe("LabelView", () => {
  it("is blind-first: the proposal appears only after submitting", async () => {
    const submitted: unknown[] = [];
    vi.stubGlobal(
      "fetch",
      vi.fn(async (url: string, init?: RequestInit) => {
        if (url === "/api/label/queue")
          return new Response(JSON.stringify(queue));
        if (url.startsWith("/api/label/search"))
          return new Response(JSON.stringify(searchPage));
        if (url === "/api/label/submit") {
          submitted.push(JSON.parse(String(init?.body)));
          return new Response(
            JSON.stringify({
              saved: true,
              proposed: { expected: "suggest", gold_edition_ids: ["OL2M"] },
              agrees_with_proposal: false,
            }),
          );
        }
        throw new Error(url);
      }),
    );
    const { container } = render(<LabelView />);
    await screen.findByText(/Query as a person typed it/);
    expect(container.textContent).not.toContain("OL2M");
    fireEvent.click(screen.getByRole("button", { name: "Search" }));
    fireEvent.click(await screen.findByLabelText("pick OL1M"));
    fireEvent.change(screen.getByLabelText("Your labeler id"), {
      target: { value: "ob" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Save label" }));
    await waitFor(() =>
      expect(screen.getByText(/Drafted proposal/)).toBeTruthy(),
    );
    expect(container.textContent).toContain("OL2M");
    expect(submitted[0]).toMatchObject({
      draft_id: "dev-001",
      labeler: "ob",
      expected: "suggest",
      gold_edition_ids: ["OL1M"],
    });
  });

  it("shows totals and truncation, and skipping never reveals the proposal", async () => {
    const calls: string[] = [];
    vi.stubGlobal(
      "fetch",
      vi.fn(async (url: string) => {
        calls.push(url);
        if (url === "/api/label/queue")
          return new Response(JSON.stringify(queue));
        if (url.startsWith("/api/label/search"))
          return new Response(JSON.stringify(searchPage));
        if (url === "/api/label/skip")
          return new Response(JSON.stringify({ skipped: true }));
        throw new Error(url);
      }),
    );
    const { container } = render(<LabelView />);
    await screen.findByText(/What am I deciding/);
    fireEvent.click(screen.getByRole("button", { name: "Search" }));
    await screen.findByText(
      /Showing 1–1 of 120 matching records \(more on the next page\)/,
    );
    expect(screen.getByRole("button", { name: "Next page →" })).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Next page →" }));
    await waitFor(() =>
      expect(calls.some((c) => c.includes("offset=50"))).toBe(true),
    );
    fireEvent.change(screen.getByLabelText("Your labeler id"), {
      target: { value: "ob" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Skip for now" }));
    await screen.findByText(
      /Nothing was labeled and the proposal stays hidden/,
    );
    expect(container.textContent).not.toContain("Drafted proposal");
  });
});
