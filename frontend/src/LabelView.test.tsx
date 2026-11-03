import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { LabelView } from "./LabelView";

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

const queue = {
  items: [{ draft_id: "dev-001", split: "dev", query: { title: "Dune", physical_format: "paperback" }, template: "t", labeled: false }],
  reasons: ["underspecified", "out_of_corpus"],
  labeled: 0,
  total: 1,
};
const rows = [
  { edition_id: "OL1M", work_id: "OL1W", title: "Dune", subtitle: null, authors: ["Frank Herbert"], publishers: ["Ace"], publish_year: 1990, physical_format: "paperback", edition_name: null, languages: ["eng"], isbn_13: [], isbn_10: [] },
];

describe("LabelView", () => {
  it("is blind-first: the proposal appears only after submitting", async () => {
    const submitted: unknown[] = [];
    vi.stubGlobal(
      "fetch",
      vi.fn(async (url: string, init?: RequestInit) => {
        if (url === "/api/label/queue") return new Response(JSON.stringify(queue));
        if (url.startsWith("/api/label/search")) return new Response(JSON.stringify(rows));
        if (url === "/api/label/submit") {
          submitted.push(JSON.parse(String(init?.body)));
          return new Response(JSON.stringify({ saved: true, proposed: { expected: "suggest", gold_edition_ids: ["OL2M"] }, agrees_with_proposal: false }));
        }
        throw new Error(url);
      }),
    );
    const { container } = render(<LabelView />);
    await screen.findByText(/Query as a person typed it/);
    expect(container.textContent).not.toContain("OL2M");
    fireEvent.click(screen.getByRole("button", { name: "Search" }));
    fireEvent.click(await screen.findByLabelText("pick OL1M"));
    fireEvent.change(screen.getByLabelText("Your labeler id"), { target: { value: "ob" } });
    fireEvent.click(screen.getByRole("button", { name: "Save label" }));
    await waitFor(() => expect(screen.getByText(/Drafted proposal/)).toBeTruthy());
    expect(container.textContent).toContain("OL2M");
    expect(submitted[0]).toMatchObject({ draft_id: "dev-001", labeler: "ob", expected: "suggest", gold_edition_ids: ["OL1M"] });
  });
});
