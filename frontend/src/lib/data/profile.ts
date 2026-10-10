import "server-only";

import { cache } from "react";

import { db } from "@/lib/firebase/admin";
import type { Profile } from "@/generated/types";

import { fromSnapshot, type WithId } from "./convert";

export const getProfile = cache(
  async (): Promise<WithId<Profile> | null> => {
    const snap = await db().collection("profile").doc("main").get();
    const profile = fromSnapshot<Profile>(snap);
    return profile?.visibility === "public" ? profile : null;
  },
);
