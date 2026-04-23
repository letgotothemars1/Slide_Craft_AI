import { FileText, Loader2, Trash2, Upload } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

interface DocumentUploadCardProps {
  attachedFileName: string | null;
  isUploading: boolean;
  disabled?: boolean;
  onUpload: (file: File) => void | Promise<void>;
  onClear: () => void;
}

export default function DocumentUploadCard({
  attachedFileName,
  isUploading,
  disabled,
  onUpload,
  onClear,
}: DocumentUploadCardProps) {
  const hasDocument = Boolean(attachedFileName);

  return (
    <div className="rounded-xl border bg-card p-4 shadow-card space-y-3">
      <div className="space-y-1">
        <h2 className="text-sm font-semibold">Upload source document</h2>
        <p className="text-xs text-muted-foreground">Optional. Supported format: PDF.</p>
      </div>

      <div className="space-y-2">
        <Input
          type="file"
          accept="application/pdf,.pdf"
          disabled={disabled || isUploading}
          onChange={(event) => {
            const file = event.target.files?.[0];
            if (file) {
              void onUpload(file);
            }
            // Allow selecting the same file again if needed.
            event.currentTarget.value = "";
          }}
        />

        {isUploading && (
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <Loader2 className="h-3.5 w-3.5 animate-spin" />
            Uploading PDF...
          </div>
        )}
      </div>

      <div className="rounded-lg border bg-background/50 px-3 py-2 text-sm">
        {hasDocument ? (
          <div className="space-y-1">
            <div className="flex items-center justify-between gap-2">
              <div className="flex items-center gap-2 min-w-0">
                <FileText className="h-4 w-4 shrink-0 text-primary" />
                <span className="truncate font-medium">{attachedFileName}</span>
              </div>
              <Button
                type="button"
                size="sm"
                variant="ghost"
                className="h-7 px-2 text-muted-foreground"
                onClick={onClear}
                disabled={disabled || isUploading}
              >
                <Trash2 className="h-4 w-4" />
              </Button>
            </div>
            <p className="text-xs text-muted-foreground">
              Presentation will be generated using this document as source context.
            </p>
          </div>
        ) : (
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <Upload className="h-3.5 w-3.5" />
            No source document attached. Presentation will be generated from prompt only.
          </div>
        )}
      </div>
    </div>
  );
}
