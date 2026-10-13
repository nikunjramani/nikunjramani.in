/** "just now", "5m ago", "3h ago", "2d ago" — for an ISO timestamp or epoch milliseconds. */
export function timeAgo(when: string | number | null | undefined): string {
  if (when === null || when === undefined || when === "") return "";
  const minutes = Math.round((Date.now() - new Date(when).getTime()) / 60_000);
  if (minutes < 1) return "just now";
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.round(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  return `${Math.round(hours / 24)}d ago`;
}
