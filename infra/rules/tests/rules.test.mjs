/**
 * Firestore rules tests.
 *
 * The emulator alone does not prove the rules are right — you have to assert against them.
 * These cover the three claims docs/plan/03-security.md makes.
 */
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test, describe } from "node:test";
import {
  initializeTestEnvironment,
  assertFails,
  assertSucceeds,
} from "@firebase/rules-unit-testing";
import { doc, getDoc, setDoc } from "firebase/firestore";

const env = await initializeTestEnvironment({
  projectId: "demo-rules",
  firestore: {
    rules: readFileSync(new URL("../firestore.rules", import.meta.url), "utf8"),
    host: "127.0.0.1",
    port: 8080,
  },
});

// Seed through the admin context, which bypasses rules — this is how real content arrives,
// since the Python API writes with admin credentials.
await env.withSecurityRulesDisabled(async (ctx) => {
  const db = ctx.firestore();
  await setDoc(doc(db, "projects/published"), { title: "Live", visibility: "public" });
  await setDoc(doc(db, "projects/draft"), { title: "Draft", visibility: "draft" });
  await setDoc(doc(db, "profile/main"), { name: "N", visibility: "public" });
  await setDoc(doc(db, "profile/no-visibility"), { name: "oops" });
  await setDoc(doc(db, "contact_messages/m1"), { email: "a@b.c" });
});

const anon = env.unauthenticatedContext().firestore();
const admin = env.authenticatedContext("uid-1", { admin: true }).firestore();

describe("firestore rules", () => {
  test("anonymous can read published content", async () => {
    await assertSucceeds(getDoc(doc(anon, "projects/published")));
    await assertSucceeds(getDoc(doc(anon, "profile/main")));
  });

  test("anonymous cannot read drafts", async () => {
    await assertFails(getDoc(doc(anon, "projects/draft")));
  });

  test("a document missing `visibility` is unreadable", async () => {
    // The trap called out in 03-security.md: null != 'public', so the read is denied
    // and the site renders empty with no useful error.
    await assertFails(getDoc(doc(anon, "profile/no-visibility")));
  });

  test("anonymous cannot write", async () => {
    await assertFails(setDoc(doc(anon, "projects/published"), { title: "hacked" }));
  });

  test("even an admin client cannot write — ADR 0007", async () => {
    await assertFails(setDoc(doc(admin, "projects/published"), { title: "via client" }));
  });

  test("contact_messages is invisible to everyone", async () => {
    await assertFails(getDoc(doc(anon, "contact_messages/m1")));
    await assertFails(getDoc(doc(admin, "contact_messages/m1")));
  });

  test("an unlisted collection is private by default", async () => {
    await assertFails(getDoc(doc(anon, "audit_log/x")));
    await assertFails(getDoc(doc(anon, "some_future_collection/x")));
  });
});

process.on("exit", () => env.cleanup());
