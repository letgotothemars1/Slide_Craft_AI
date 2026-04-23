import { Button } from "@/components/ui/button";
import { Download } from "lucide-react";

interface Props {
  pptxUrl: string | null;
  pdfUrl: string | null;
}

export default function DownloadButtons({ pptxUrl, pdfUrl }: Props) {
  if (!pptxUrl && !pdfUrl) return null;

  return (
    <div className="flex flex-wrap gap-3">
      {pptxUrl && (
        <Button asChild variant="default" className="gap-2">
          <a href={pptxUrl} download>
            <Download className="h-4 w-4" />
            Скачать PPTX
          </a>
        </Button>
      )}
      {pdfUrl && (
        <Button asChild variant="outline" className="gap-2">
          <a href={pdfUrl} download>
            <Download className="h-4 w-4" />
            Скачать PDF
          </a>
        </Button>
      )}
    </div>
  );
}
