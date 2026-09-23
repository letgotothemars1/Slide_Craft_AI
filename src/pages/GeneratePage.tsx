import { useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import AppHeader from "@/components/AppHeader";
import Reveal from "@/components/Reveal";
import PromptForm from "@/components/PromptForm";
import { type GenerateRequest, generatePresentation, uploadDocument } from "@/lib/api";
import { addToHistory } from "@/lib/history";
import { track } from "@/lib/analytics";
import { useLanguage } from "@/context/LanguageContext";
import { toast } from "sonner";

export default function GeneratePage() {
  const navigate = useNavigate();
  const { t } = useLanguage();
  const [loading, setLoading] = useState(false);
  const [uploadingDocument, setUploadingDocument] = useState(false);
  const [attachedDocumentId, setAttachedDocumentId] = useState<string | null>(null);
  const [attachedDocumentName, setAttachedDocumentName] = useState<string | null>(null);

  const handleDocumentUpload = useCallback(
    async (file: File) => {
      const isPdfFile = file.type === "application/pdf" || file.name.toLowerCase().endsWith(".pdf");
      if (!isPdfFile) {
        toast.error(t("gen.error.pdfOnly"));
        return;
      }

      setUploadingDocument(true);
      try {
        const { document_id } = await uploadDocument(file);
        setAttachedDocumentId(document_id);
        setAttachedDocumentName(file.name);
        toast.success(t("gen.ok.attached"));
      } catch (err: any) {
        toast.error(err?.message || t("gen.error.upload"));
      } finally {
        setUploadingDocument(false);
      }
    },
    [t],
  );

  const handleDocumentClear = useCallback(() => {
    setAttachedDocumentId(null);
    setAttachedDocumentName(null);
  }, []);

  const handleSubmit = useCallback(
    async (data: GenerateRequest) => {
      setLoading(true);
      // Funnel step: user actually pressed "Generate". Capture key form choices.
      track("generate_click", {
        audience: data.audience,
        style: data.style,
        language: data.language,
        format: data.format,
        slides: data.slides,
        with_document: Boolean(attachedDocumentId),
      });
      try {
        const payload: GenerateRequest = {
          ...data,
          document_id: attachedDocumentId,
        };
        const jobId = await generatePresentation(payload);
        addToHistory({
          job_id: jobId,
          prompt_snippet: data.prompt.slice(0, 80),
          created_at: new Date().toISOString(),
          status: "queued",
        });
        navigate(`/jobs/${jobId}`);
      } catch (err: any) {
        toast.error(err.message || t("gen.error.generate"));
      } finally {
        setLoading(false);
      }
    },
    [attachedDocumentId, navigate, t],
  );


  return (
    <div className="flex min-h-screen flex-col bg-background">
      <AppHeader />

      <main className="flex-1 px-4 py-14 sm:py-20">
        <div className="container max-w-3xl">
          <Reveal className="mb-10 space-y-3 text-center">
            <h1 className="font-display text-3xl font-extrabold tracking-tight sm:text-4xl">
              {t("gen.title")}
            </h1>
            <p className="mx-auto max-w-xl text-sm leading-relaxed text-muted-foreground sm:text-base">
              {t("gen.subtitle")}
            </p>
          </Reveal>

          <Reveal delay={100}>
            <PromptForm
              onSubmit={handleSubmit}
              isLoading={loading}
              attachedFileName={attachedDocumentName}
              isUploading={uploadingDocument}
              onUpload={handleDocumentUpload}
              onClearFile={handleDocumentClear}
            />
          </Reveal>
        </div>
      </main>
    </div>
  );
}
