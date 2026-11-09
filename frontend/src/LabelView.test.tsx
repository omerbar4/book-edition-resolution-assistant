import {
  cleanup,
  fireEvent,
  render,
  waitFor,
  within,
} from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { LabelView } from "./LabelView";

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

// Queries are scoped to each test's own container (not the global `screen`): if a test
// ever times out, its still-running code cannot find or click elements rendered by the
// next test. That leak once made a timed-out test submit a label through the next test's
// fetch stub.
type Ui = ReturnType<typeof within>;

// LabelView enables Search only after an effect copies the case title into the search
// box. That effect can run after the case is already visible, and a click on the still
// disabled button is silently ignored, so wait until it is enabled before clicking.
async function clickSearch(ui: Ui) {
  await waitFor(() =>
    expect(
      (ui.getByRole("button", { name: "Search" }) as HTMLButtonElement).disabled,
    ).toBe(false),
  );
  fireEvent.click(ui.getByRole("button", { name: "Search" }));
}

const queue = {
  items: [
    {
      draft_id: "dev-001",
      split: "dev",
      query: { title: "Dune", physical_format: "paperback" },
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
              template: "secret_template_name",
              template_note: null,
            }),
          );
        }
        throw new Error(url);
      }),
    );
    const { container } = render(<LabelView />);
    const ui = within(container);
    await ui.findByText(/Query as a person typed it/);
    expect(container.textContent).not.toContain("OL2M");
    await clickSearch(ui);
    fireEvent.click(await ui.findByLabelText("pick OL1M"));
    fireEvent.change(ui.getByLabelText("Your labeler id"), {
      target: { value: "ob" },
    });
    fireEvent.click(ui.getByLabelText(/One specific edition/));
    expect(container.textContent).not.toContain("secret_template_name");
    fireEvent.click(ui.getByRole("button", { name: "Save label" }));
    await waitFor(() =>
      expect(ui.getByText(/Drafted proposal/)).toBeTruthy(),
    );
    expect(container.textContent).toContain("OL2M");
    expect(container.textContent).toContain(
      "Generator template: secret_template_name",
    );
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
    const ui = within(container);
    await ui.findByText(/What am I deciding/);
    await clickSearch(ui);
    await ui.findByText(
      /Showing 1–1 of 120 matching records \(more on the next page\)/,
    );
    expect(ui.getByRole("button", { name: "Next page →" })).toBeTruthy();
    fireEvent.click(ui.getByRole("button", { name: "Next page →" }));
    await waitFor(() =>
      expect(calls.some((c) => c.includes("offset=50"))).toBe(true),
    );
    fireEvent.change(ui.getByLabelText("Your labeler id"), {
      target: { value: "ob" },
    });
    fireEvent.click(ui.getByRole("button", { name: "Skip for now" }));
    await ui.findByText(
      /Nothing was labeled and the proposal stays hidden/,
    );
    expect(container.textContent).not.toContain("Drafted proposal");
  });
  it("has no default answer and enables Save only for a complete answer", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async (url: string) => {
        if (url === "/api/label/queue")
          return new Response(JSON.stringify(queue));
        if (url.startsWith("/api/label/search"))
          return new Response(JSON.stringify(searchPage));
        throw new Error(url);
      }),
    );
    const { container } = render(<LabelView />);
    const ui = within(container);
    await ui.findByText(/Query as a person typed it/);
    const one = ui.getByLabelText(/One specific edition/) as HTMLInputElement;
    const review = ui.getByLabelText(
      /Human review \(abstain\)/,
    ) as HTMLInputElement;
    // nothing is selected by default and nothing reads like a stated answer
    expect(one.checked).toBe(false);
    expect(review.checked).toBe(false);
    expect(container.querySelectorAll("input:checked").length).toBe(0);
    expect(container.textContent).not.toContain("Correct behavior is");
    expect(container.textContent).not.toContain("Generator template");
    const save = () =>
      ui.getByRole("button", { name: "Save label" }) as HTMLButtonElement;
    fireEvent.change(ui.getByLabelText("Your labeler id"), {
      target: { value: "ob" },
    });
    expect(save().disabled).toBe(true);
    // a picked record without choosing an answer is not enough
    await clickSearch(ui);
    fireEvent.click(await ui.findByLabelText("pick OL1M"));
    expect(save().disabled).toBe(true);
    fireEvent.click(one);
    expect(save().disabled).toBe(false);
    // abstain needs a reason
    fireEvent.click(review);
    expect(save().disabled).toBe(true);
    fireEvent.change(ui.getByRole("combobox"), {
      target: { value: "out_of_corpus" },
    });
    expect(save().disabled).toBe(false);
    // "one edition" with no record ticked is not enough
    fireEvent.click(ui.getByLabelText("pick OL1M"));
    fireEvent.click(one);
    expect(save().disabled).toBe(true);
  });

  it("opens on the first unlabeled case even when it is exposed, and says it won't count", async () => {
    const q = {
      ...queue,
      items: [
        { ...queue.items[0], draft_id: "dev-001", labeled: true, status: "practice" },
        { ...queue.items[0], draft_id: "dev-002", labeled: false, status: "exposed" },
      ],
      total: 2,
      labeled: 1,
      independent: 0,
      practice: 1,
      exposed: 1,
    };
    vi.stubGlobal(
      "fetch",
      vi.fn(async (url: string) => {
        if (url === "/api/label/queue") return new Response(JSON.stringify(q));
        throw new Error(url);
      }),
    );
    const ui = within(render(<LabelView />).container);
    await ui.findByText(/dev-002 \(2\/2\)/);
    expect(
      ui.getByText(/a label here will not count as independent/),
    ).toBeTruthy();
    expect(ui.getByText(/1 exposed before labeling \(not counted\)/)).toBeTruthy();
  });

  it("after_batch: a save shows nothing about the proposal until the batch is complete", async () => {
    let labeled = 0;
    const q = () => ({
      ...queue,
      reveal_mode: "after_batch",
      revealed: false,
      labeled,
      items: [{ ...queue.items[0], labeled: labeled > 0 }],
    });
    vi.stubGlobal(
      "fetch",
      vi.fn(async (url: string) => {
        if (url === "/api/label/queue") return new Response(JSON.stringify(q()));
        if (url.startsWith("/api/label/search"))
          return new Response(JSON.stringify(searchPage));
        if (url === "/api/label/submit") {
          labeled = 1;
          return new Response(
            JSON.stringify({ saved: true, reveal: "after_batch", remaining: 0 }),
          );
        }
        if (url === "/api/label/reveal")
          return new Response(
            JSON.stringify({
              items: [
                {
                  draft_id: "dev-001",
                  your_label: { expected: "suggest", gold_edition_ids: ["OL1M"] },
                  proposed: { expected: "suggest", gold_edition_ids: ["OL2M"] },
                  agrees_with_proposal: false,
                  template: "secret_template_name",
                },
              ],
              agree: 0,
              total: 1,
              note: "measures the drafter",
            }),
          );
        throw new Error(url);
      }),
    );
    const { container } = render(<LabelView />);
    const ui = within(container);
    await ui.findByText(/Query as a person typed it/);
    await clickSearch(ui);
    fireEvent.click(await ui.findByLabelText("pick OL1M"));
    fireEvent.change(ui.getByLabelText("Your labeler id"), {
      target: { value: "ob" },
    });
    fireEvent.click(ui.getByLabelText(/One specific edition/));
    fireEvent.click(ui.getByRole("button", { name: "Save label" }));
    await ui.findByText(/stay hidden until every case/);
    expect(container.textContent).not.toContain("OL2M");
    expect(container.textContent).not.toContain("secret_template_name");
    expect(container.textContent).not.toContain("Drafted proposal (");
    expect(
      (ui.getByRole("button", { name: "Save label" }) as HTMLButtonElement).disabled,
    ).toBe(true);
    fireEvent.click(
      await ui.findByRole("button", {
        name: "Show drafted proposals for the whole batch",
      }),
    );
    await ui.findByText(/0\/1 match your labels/);
    expect(container.textContent).toContain("OL2M");
    expect(container.textContent).toContain("secret_template_name");
  });

  it("never-reveal queues confirm the save and show no reveal button", async () => {
    let labeled = 0;
    const q = () => ({
      ...queue,
      reveal_mode: "never",
      labeled,
      items: [{ ...queue.items[0], labeled: labeled > 0 }],
    });
    vi.stubGlobal(
      "fetch",
      vi.fn(async (url: string) => {
        if (url === "/api/label/queue") return new Response(JSON.stringify(q()));
        if (url.startsWith("/api/label/search"))
          return new Response(JSON.stringify(searchPage));
        if (url === "/api/label/submit") {
          labeled = 1;
          return new Response(
            JSON.stringify({ saved: true, reveal: "never", remaining: 0 }),
          );
        }
        throw new Error(url);
      }),
    );
    const ui = within(render(<LabelView />).container);
    await ui.findByText(/Query as a person typed it/);
    await clickSearch(ui);
    fireEvent.click(await ui.findByLabelText("pick OL1M"));
    fireEvent.change(ui.getByLabelText("Your labeler id"), {
      target: { value: "ob" },
    });
    fireEvent.click(ui.getByLabelText(/One specific edition/));
    fireEvent.click(ui.getByRole("button", { name: "Save label" }));
    await ui.findByText(/never shown for this queue/);
    expect(ui.queryByText(/Held-out queue/)).toBeNull(); // dev split in this fixture
    expect(
      ui.queryByRole("button", {
        name: "Show drafted proposals for the whole batch",
      }),
    ).toBeNull();
  });
});
