import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useLanguage } from "@/context/LanguageContext";
import { Check, Copy, Link2 } from "lucide-react";

interface Props {
  jobId: string;
}

export default function ShareLink({ jobId }: Props) {
  const { t } = useLanguage();
  const [copied, setCopied] = useState(false);
  const url = `${window.location.origin}/jobs/${jobId}`;

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(url);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Clipboard access can be denied; the field is readable and selectable,
      // so the user can still copy by hand.
    }
  };

  return (
    <div className="space-y-2">
      <h2 className="flex items-center gap-1.5 text-sm font-medium text-muted-foreground">
        <Link2 className="h-3.5 w-3.5" aria-hidden="true" />
        {t("job.share")}
      </h2>
      <div className="flex gap-2">
        <Input value={url} readOnly aria-label={t("job.share")} className="h-11 font-mono text-xs" />
        <Button
          variant="outline"
          size="icon"
          onClick={copy}
          aria-label={t("job.copyLink")}
          className="h-11 w-11 shrink-0"
        >
          {copied ? (
            <Check className="h-4 w-4 text-success-strong" aria-hidden="true" />
          ) : (
            <Copy className="h-4 w-4" aria-hidden="true" />
          )}
        </Button>
      </div>
      {/* Announced only when it flips, so the confirmation is not silent. */}
      <span role="status" className="sr-only">
        {copied ? t("job.copied") : ""}
      </span>
    </div>
  );
}
