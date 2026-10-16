import { describe, expect, it } from "vitest";

import { toMergePatch } from "./merge-patch";

describe("toMergePatch", () => {
  it("sends only what changed", () => {
    expect(toMergePatch({ title: "A", summary: "S" }, { title: "B", summary: "S" })).toEqual({
      title: "B",
    });
  });

  it("turns a cleared field into an explicit null", () => {
    expect(toMergePatch({ subtitle: "x", title: "A" }, { subtitle: undefined, title: "A" })).toEqual({
      subtitle: null,
    });
    expect(toMergePatch({ subtitle: "x" }, {})).toEqual({ subtitle: null });
  });

  it("removes a whole section, and treats an emptied one as removed", () => {
    expect(toMergePatch({ cover: { url: "u", alt: "a" } }, { cover: undefined })).toEqual({ cover: null });
    expect(toMergePatch({ client: { name: "Acme" } }, { client: { name: undefined } })).toEqual({
      client: null,
    });
  });

  it("recurses into objects", () => {
    expect(
      toMergePatch(
        { content: { overview: "o", problem: "p" } },
        { content: { overview: "o", problem: undefined, approach: "new" } },
      ),
    ).toEqual({ content: { problem: null, approach: "new" } });
  });

  it("replaces arrays wholesale, and only when they differ", () => {
    expect(toMergePatch({ tags: ["a", "b"] }, { tags: ["a", "b"] })).toEqual({});
    expect(toMergePatch({ tags: ["a", "b"] }, { tags: ["b"] })).toEqual({ tags: ["b"] });
  });

  it("ignores key order and stored nulls", () => {
    expect(toMergePatch({ a: { x: 1, y: 2 }, gone: null }, { a: { y: 2, x: 1 } })).toEqual({});
  });

  it("keeps false and zero as real values", () => {
    expect(toMergePatch({ featured: true, order: 3 }, { featured: false, order: 0 })).toEqual({
      featured: false,
      order: 0,
    });
  });
});
