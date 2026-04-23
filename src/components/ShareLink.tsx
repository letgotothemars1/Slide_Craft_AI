import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Check, Copy, Link } from "lucide-react";

interface Props {
  jobId: string;
}

export default function ShareLink({ jobId }: Props) {
  const [copied, setCopied] = useState(false);
  const url = `${window.location.origin}/jobs/${jobId}`;

  const copy = async () => {
    await navigator.clipboard.writeText(url);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="space-y-2">
      <h3 className="flex items-center gap-1.5 text-sm font-medium text-muted-foreground">
        <Link className="h-3.5 w-3.5" />
        Поделиться
      </h3>
      <div className="flex gap-2">
        <Input value={url} readOnly className="font-mono text-xs" />
        <Button variant="outline" size="icon" onClick={copy}>
          {copied ? <Check className="h-4 w-4 text-success" /> : <Copy className="h-4 w-4" />}
        </Button>
      </div>
    </div>
  );
}
