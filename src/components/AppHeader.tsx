import { Link } from "react-router-dom";
import { Plus, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import LanguageToggle from "@/components/LanguageToggle";
import UserAvatarButton from "@/components/UserAvatarButton";
import { useAuth } from "@/context/AuthContext";
import { useLanguage } from "@/context/LanguageContext";

interface Props {
  /** Logo and language switch only — for the auth page, where the sign-in
   *  actions would point at the page you are already on. */
  minimal?: boolean;
  /** Landing page funnel tracking; other pages have nothing to report. */
  onCtaClick?: (source: string) => void;
}

/**
 * The one header every page uses.
 *
 * Each page used to render its own, which is how they drifted apart: two
 * different heights, three different nav sets, and the language switch on
 * exactly one of them.
 */
export default function AppHeader({ minimal, onCtaClick }: Props) {
  const { user } = useAuth();
  const { t } = useLanguage();

  return (
    <header className="sticky top-0 z-50 border-b border-border/60 bg-card/70 backdrop-blur-md">
      <div className="container flex h-14 items-center justify-between">
        <Link
          to="/"
          aria-label="SlideCraft AI"
          className="flex shrink-0 items-center gap-2 whitespace-nowrap rounded font-display text-base font-bold focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 sm:text-lg"
        >
          <Sparkles className="h-5 w-5 text-primary" aria-hidden="true" />
          {/* Wordmark drops below sm. On a 375px phone the row also carries the
              language switch, the create button and the avatar; shrinking any
              of those would put a touch target under 44px, and the mark alone
              still identifies the product. */}
          <span className="hidden xs:inline">SlideCraft AI</span>
        </Link>

        {/* Touch targets stay ≥44px on phones, compact from sm upward. */}
        <div className="flex items-center gap-1.5 sm:gap-2">
          <LanguageToggle />

          {minimal ? null : user ? (
            <>
              {/* Icon-only on phones. With the language switch and the avatar
                  also in the row, a labelled button pushed the header past
                  375px and the whole page scrolled sideways. */}
              <Button
                size="sm"
                asChild
                className="h-11 w-11 rounded-full p-0 sm:h-9 sm:w-auto sm:rounded-md sm:px-3"
              >
                <Link
                  to="/generate"
                  onClick={() => onCtaClick?.("header")}
                  aria-label={t("nav.create")}
                >
                  <Plus className="h-5 w-5 sm:hidden" aria-hidden="true" />
                  <span className="hidden sm:inline">{t("nav.create")}</span>
                </Link>
              </Button>
              {/* Account, not log out: history and sign-out both live inside. */}
              <UserAvatarButton />
            </>
          ) : (
            <>
              {/* Hidden on phones: the CTA beside it already leads to /auth,
                  and the row would otherwise overflow at 375px. */}
              <Link
                to="/auth"
                className="hidden items-center rounded-md px-3 py-1.5 text-sm text-muted-foreground transition-colors hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 sm:inline-flex"
              >
                {t("nav.login")}
              </Link>
              <Button size="sm" asChild className="h-11 sm:h-9">
                <Link to="/auth" onClick={() => onCtaClick?.("header")}>
                  <span className="sm:hidden">{t("nav.signupShort")}</span>
                  <span className="hidden sm:inline">{t("nav.signup")}</span>
                </Link>
              </Button>
            </>
          )}
        </div>
      </div>
    </header>
  );
}
