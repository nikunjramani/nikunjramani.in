"use client";

import { useSyncExternalStore } from "react";

const emptySubscribe = () => () => {};

/**
 * True once the client has hydrated, false during SSR and the first client render.
 * The canonical `useState` + `useEffect(() => setMounted(true), [])` pattern works but
 * costs an extra render pass and trips eslint-plugin-react-hooks' set-state-in-effect
 * rule; useSyncExternalStore's getServerSnapshot/getSnapshot split expresses the same
 * "different value on server vs. client" fact without an effect at all.
 */
export function useMounted(): boolean {
  return useSyncExternalStore(
    emptySubscribe,
    () => true,
    () => false,
  );
}
