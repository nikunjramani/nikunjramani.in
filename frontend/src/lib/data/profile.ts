import "server-only";

import { unstable_cache } from "next/cache";

import { db } from "@/lib/firebase/admin";
import type { Profile } from "@/generated/types";

import { fromSnapshot, type WithId } from "./convert";

export const getProfile = unstable_cache(
  async (): Promise<WithId<Profile> | null> => {
    const snap = await db().collection("profile").doc("main").get();
    return fromSnapshot<Profile>(snap);
  },
  ["profile-main"],
  { tags: ["profile"], revalidate: 3600 },
);
