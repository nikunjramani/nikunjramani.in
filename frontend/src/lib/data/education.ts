import "server-only";

import { cache } from "react";

import type { Education } from "@/generated/types";

import { listPublished } from "./shared";
import type { WithId } from "./convert";

export const getEducations = cache(
  (): Promise<WithId<Education>[]> => listPublished<Education>("education"),
);
