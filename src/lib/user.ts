import type { AuthUser } from "@/lib/auth";

type MaybeUser = Pick<AuthUser, "email" | "username" | "firstName" | "lastName"> | null | undefined;

/**
 * Identity helpers, all in one place.
 *
 * Every user has an email; the rest of the profile is optional and was added
 * later, so each helper falls back down a chain rather than assuming a name
 * exists: real name → username → email local part.
 */

/** Full name when both parts are set, otherwise whichever one is. */
export function fullName(user: MaybeUser): string {
  return [user?.firstName, user?.lastName].filter(Boolean).join(" ").trim();
}

/** What to greet the person with: first name, else username, else email handle. */
export function greetingName(user: MaybeUser): string {
  return user?.firstName?.trim() || user?.username?.trim() || emailHandle(user);
}

/** The strongest identity label available, for headings. */
export function displayName(user: MaybeUser): string {
  return fullName(user) || user?.username?.trim() || emailHandle(user);
}

/** "letgotothemars1@gmail.com" → "letgotothemars1" */
export function emailHandle(user: MaybeUser): string {
  if (!user?.email) return "";
  return user.email.split("@")[0] ?? user.email;
}

/** Up to two letters for the avatar: "Илья Попов" → "ИП", "ilyap@…" → "IL". */
export function userInitials(user: MaybeUser): string {
  const first = user?.firstName?.trim();
  const last = user?.lastName?.trim();
  if (first && last) return (first[0] + last[0]).toUpperCase();
  if (first) return first.slice(0, 2).toUpperCase();

  const source = user?.username?.trim() || emailHandle(user);
  if (!source) return "?";

  const parts = source.split(/[._-]+/).filter(Boolean);
  if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase();
  return source.slice(0, 2).toUpperCase();
}
