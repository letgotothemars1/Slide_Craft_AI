import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import AppHeader from "@/components/AppHeader";
import Reveal from "@/components/Reveal";
import HistoryList from "@/components/HistoryList";
import { useAuth } from "@/context/AuthContext";
import { useLanguage } from "@/context/LanguageContext";
import { clearHistory, getHistory, type HistoryEntry } from "@/lib/history";
import { formatDateTime } from "@/lib/i18n";
import { displayName, fullName, userInitials } from "@/lib/user";
import { toast } from "sonner";
import { LogOut, ShieldCheck, Trash2, Lock, User as UserIcon, Loader2 } from "lucide-react";

const MIN_PASSWORD = 8;

export default function AccountPage() {
  const { user, session, isAdmin, logout, updateProfile, changePassword } = useAuth();
  const { t, language } = useLanguage();
  const navigate = useNavigate();

  const [entries, setEntries] = useState<HistoryEntry[]>([]);

  // Profile form, seeded from the session once it is available.
  const [username, setUsername] = useState("");
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [savingProfile, setSavingProfile] = useState(false);
  const [profileError, setProfileError] = useState<string | null>(null);

  const [current, setCurrent] = useState("");
  const [next, setNext] = useState("");
  const [repeat, setRepeat] = useState("");
  const [savingPassword, setSavingPassword] = useState(false);
  const [passwordError, setPasswordError] = useState<string | null>(null);

  useEffect(() => {
    setEntries(getHistory());
  }, []);

  useEffect(() => {
    if (!user) return;
    setUsername(user.username ?? "");
    setFirstName(user.firstName ?? "");
    setLastName(user.lastName ?? "");
  }, [user]);

  const handleClearHistory = () => {
    clearHistory();
    setEntries([]);
  };

  const handleLogout = async () => {
    await logout();
    navigate("/", { replace: true });
  };

  const handleProfileSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setProfileError(null);
    setSavingProfile(true);
    try {
      await updateProfile({
        username: username.trim() || null,
        first_name: firstName.trim() || null,
        last_name: lastName.trim() || null,
      });
      toast.success(t("account.profileSaved"));
    } catch (err: unknown) {
      // The backend sends precise messages, e.g. a taken username.
      setProfileError((err instanceof Error && err.message) || t("gen.error.generate"));
    } finally {
      setSavingProfile(false);
    }
  };

  const handlePasswordSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (next.length < MIN_PASSWORD) return setPasswordError(t("account.error.passwordShort"));
    if (next !== repeat) return setPasswordError(t("account.error.passwordMismatch"));
    if (next === current) return setPasswordError(t("account.error.passwordSame"));

    setPasswordError(null);
    setSavingPassword(true);
    try {
      await changePassword(current, next);
      setCurrent("");
      setNext("");
      setRepeat("");
      toast.success(t("account.passwordSaved"));
    } catch (err: unknown) {
      setPasswordError((err instanceof Error && err.message) || t("gen.error.generate"));
    } finally {
      setSavingPassword(false);
    }
  };

  const name = fullName(user);

  return (
    <div className="flex min-h-screen flex-col bg-background">
      <AppHeader />

      <main className="flex-1 px-4 py-12 sm:py-16">
        <div className="container max-w-3xl space-y-8">
          {/* ── identity ── */}
          <Reveal>
            <section className="relative overflow-hidden rounded-2xl border border-border bg-card p-6 shadow-card sm:p-8">
              <div
                aria-hidden="true"
                className="pointer-events-none absolute -right-20 -top-20 h-56 w-56 rounded-full bg-primary/[0.06] blur-3xl"
              />
              <div className="relative flex flex-col items-center gap-5 text-center sm:flex-row sm:items-center sm:text-left">
                <span className="inline-flex h-16 w-16 shrink-0 items-center justify-center rounded-2xl gradient-hero text-xl font-bold text-primary-foreground">
                  <span aria-hidden="true">{userInitials(user)}</span>
                </span>

                <div className="min-w-0 flex-1 space-y-1.5">
                  <div className="flex flex-wrap items-center justify-center gap-2 sm:justify-start">
                    <h1 className="font-display text-2xl font-bold tracking-tight">
                      {displayName(user)}
                    </h1>
                    {isAdmin && (
                      <Badge variant="secondary" className="gap-1 bg-primary/10 text-primary">
                        <ShieldCheck className="h-3.5 w-3.5" aria-hidden="true" />
                        {t("account.adminBadge")}
                      </Badge>
                    )}
                  </div>
                  {/* Show the username only when it is not already the heading. */}
                  {user?.username && name && (
                    <p className="text-sm text-muted-foreground">@{user.username}</p>
                  )}
                  <p className="truncate text-sm text-muted-foreground">{user?.email}</p>
                  {session?.createdAt && (
                    <p className="text-xs text-muted-foreground">
                      {t("account.memberSince")} {formatDateTime(session.createdAt, language)}
                    </p>
                  )}
                </div>

                <Button
                  variant="outline"
                  onClick={handleLogout}
                  className="h-11 shrink-0 gap-2 rounded-full px-5"
                >
                  <LogOut className="h-4 w-4" aria-hidden="true" />
                  {t("account.logout")}
                </Button>
              </div>
            </section>
          </Reveal>

          {/* ── profile ── */}
          <Reveal delay={80}>
            <section className="space-y-4 rounded-2xl border border-border bg-card p-6 shadow-card sm:p-8">
              <div className="flex items-center gap-2">
                <UserIcon className="h-4 w-4 text-muted-foreground" aria-hidden="true" />
                <h2 className="font-display text-lg font-semibold">{t("account.profile")}</h2>
              </div>

              <form onSubmit={handleProfileSubmit} className="space-y-4">
                <div className="grid gap-4 sm:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="first-name">{t("account.firstName")}</Label>
                    <Input
                      id="first-name"
                      autoComplete="given-name"
                      value={firstName}
                      onChange={(e) => setFirstName(e.target.value)}
                      className="h-11"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="last-name">{t("account.lastName")}</Label>
                    <Input
                      id="last-name"
                      autoComplete="family-name"
                      value={lastName}
                      onChange={(e) => setLastName(e.target.value)}
                      className="h-11"
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="username">{t("account.username")}</Label>
                  <Input
                    id="username"
                    autoComplete="username"
                    spellCheck={false}
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    className="h-11"
                  />
                  <p className="text-xs text-muted-foreground">{t("account.usernameHint")}</p>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="account-email">{t("account.emailLabel")}</Label>
                  <Input id="account-email" value={user?.email ?? ""} readOnly disabled className="h-11" />
                  <p className="text-xs text-muted-foreground">{t("account.emailHint")}</p>
                </div>

                {profileError && (
                  <p role="alert" className="text-sm text-destructive">
                    {profileError}
                  </p>
                )}

                <Button type="submit" disabled={savingProfile} className="h-11 rounded-full px-6">
                  {savingProfile && <Loader2 className="mr-2 h-4 w-4 animate-spin" aria-hidden="true" />}
                  {savingProfile ? t("account.saving") : t("account.saveProfile")}
                </Button>
              </form>
            </section>
          </Reveal>

          {/* ── security ── */}
          <Reveal delay={120}>
            <section className="space-y-4 rounded-2xl border border-border bg-card p-6 shadow-card sm:p-8">
              <div className="flex items-center gap-2">
                <Lock className="h-4 w-4 text-muted-foreground" aria-hidden="true" />
                <h2 className="font-display text-lg font-semibold">{t("account.security")}</h2>
              </div>

              <form onSubmit={handlePasswordSubmit} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="current-password">{t("account.currentPassword")}</Label>
                  {/* autocomplete + paste allowed: WCAG 2.2 requires that a
                      password manager can fill and that paste is not blocked. */}
                  <Input
                    id="current-password"
                    type="password"
                    autoComplete="current-password"
                    value={current}
                    onChange={(e) => setCurrent(e.target.value)}
                    className="h-11"
                  />
                </div>

                <div className="grid gap-4 sm:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="new-password">{t("account.newPassword")}</Label>
                    <Input
                      id="new-password"
                      type="password"
                      autoComplete="new-password"
                      minLength={MIN_PASSWORD}
                      value={next}
                      onChange={(e) => setNext(e.target.value)}
                      className="h-11"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="repeat-password">{t("account.repeatPassword")}</Label>
                    <Input
                      id="repeat-password"
                      type="password"
                      autoComplete="new-password"
                      value={repeat}
                      onChange={(e) => setRepeat(e.target.value)}
                      className="h-11"
                    />
                  </div>
                </div>

                {passwordError && (
                  <p role="alert" className="text-sm text-destructive">
                    {passwordError}
                  </p>
                )}

                <Button type="submit" disabled={savingPassword} className="h-11 rounded-full px-6">
                  {savingPassword && <Loader2 className="mr-2 h-4 w-4 animate-spin" aria-hidden="true" />}
                  {t("account.changePassword")}
                </Button>
              </form>
            </section>
          </Reveal>

          {/* ── history ── */}
          <Reveal delay={160}>
            <section className="space-y-4">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div className="flex items-baseline gap-2.5">
                  <h2 className="font-display text-lg font-semibold">{t("history.title")}</h2>
                  {entries.length > 0 && (
                    <span className="text-sm tabular-nums text-muted-foreground">
                      {entries.length}
                    </span>
                  )}
                </div>
                {entries.length > 0 && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={handleClearHistory}
                    className="h-11 gap-1.5 text-muted-foreground sm:h-9"
                  >
                    <Trash2 className="h-4 w-4" aria-hidden="true" />
                    {t("history.clear")}
                  </Button>
                )}
              </div>

              <HistoryList entries={entries} />
            </section>
          </Reveal>
        </div>
      </main>
    </div>
  );
}
