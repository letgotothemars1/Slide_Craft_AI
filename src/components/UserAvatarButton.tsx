import { Link } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import { useLanguage } from "@/context/LanguageContext";
import { userInitials } from "@/lib/user";
import { cn } from "@/lib/utils";

/**
 * Avatar in the header that opens the account page.
 *
 * Replaces the old "Log out" button: signing out is a once-in-a-while action
 * and does not deserve permanent real estate next to the primary CTA. It now
 * lives inside the account page, where the rest of the identity controls are.
 */
export default function UserAvatarButton({ className }: { className?: string }) {
  const { user } = useAuth();
  const { t } = useLanguage();

  if (!user) return null;

  return (
    <Link
      to="/account"
      aria-label={`${t("account.open")} — ${user.email}`}
      title={user.email}
      className={cn(
        "inline-flex h-11 w-11 shrink-0 items-center justify-center rounded-full border border-border",
        "bg-muted text-xs font-semibold tracking-wide text-foreground transition-colors",
        "hover:border-primary/40 hover:bg-primary/10 hover:text-primary",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
        "sm:h-9 sm:w-9",
        className,
      )}
    >
      {/* Initials, not a generic person glyph: at a glance it tells you *which*
          account you are signed in as. */}
      <span aria-hidden="true">{userInitials(user)}</span>
    </Link>
  );
}
