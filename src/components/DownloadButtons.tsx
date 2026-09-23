import { Button } from "@/components/ui/button";
import { useLanguage } from "@/context/LanguageContext";
import { Download } from "lucide-react";

interface Props {
  pptxUrl: string | null;
  pdfUrl: string | null;
}

export default function DownloadButtons({ pptxUrl, pdfUrl }: Props) {
  const { t } = useLanguage();
  if (!pptxUrl && !pdfUrl) return null;

  // PDF first: it is the default output format, so it leads.
  return (
    <div className="flex flex-wrap gap-3">
      {pdfUrl && (
        <Button asChild className="h-11 gap-2 rounded-full px-6">
          <a href={pdfUrl} download>
            <Download className="h-4 w-4" aria-hidden="true" />
            {t("job.downloadPdf")}
          </a>
        </Button>
      )}
      {pptxUrl && (
        <Button asChild variant="outline" className="h-11 gap-2 rounded-full px-6">
          <a href={pptxUrl} download>
            <Download className="h-4 w-4" aria-hidden="true" />
            {t("job.downloadPptx")}
          </a>
        </Button>
      )}
    </div>
  );
}
