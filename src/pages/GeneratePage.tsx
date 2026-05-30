import { useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import PromptForm from "@/components/PromptForm";
import DocumentUploadCard from "@/components/DocumentUploadCard";
import { type GenerateRequest, generatePresentation, uploadDocument } from "@/lib/api";
import { addToHistory } from "@/lib/history";
import { track } from "@/lib/analytics";
import { Sparkles } from "lucide-react";
import { toast } from "sonner";
import { useAuth } from "@/context/AuthContext";

export default function GeneratePage() {
  const navigate = useNavigate();
  const { logout } = useAuth();
  const [loading, setLoading] = useState(false);
  const [uploadingDocument, setUploadingDocument] = useState(false);
  const [attachedDocumentId, setAttachedDocumentId] = useState<string | null>(null);
  const [attachedDocumentName, setAttachedDocumentName] = useState<string | null>(null);

  const handleDocumentUpload = useCallback(async (file: File) => {
    const isPdfFile = file.type === "application/pdf" || file.name.toLowerCase().endsWith(".pdf");
    if (!isPdfFile) {
      toast.error("Можно загрузить только PDF-файл");
      return;
    }

    setUploadingDocument(true);
    try {
      const { document_id } = await uploadDocument(file);
      setAttachedDocumentId(document_id);
      setAttachedDocumentName(file.name);
      toast.success("Документ прикреплён");
    } catch (err: any) {
      toast.error(err?.message || "Не удалось загрузить документ");
    } finally {
      setUploadingDocument(false);
    }
  }, []);

  const handleDocumentClear = useCallback(() => {
    setAttachedDocumentId(null);
    setAttachedDocumentName(null);
  }, []);

  const handleSubmit = useCallback(async (data: GenerateRequest) => {
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
      toast.error(err.message || "Ошибка при запуске генерации");
    } finally {
      setLoading(false);
    }
  }, [attachedDocumentId, navigate]);

  const handleLogout = useCallback(async () => {
    await logout();
    navigate("/", { replace: true });
  }, [logout, navigate]);

  return (
    <div className="min-h-screen flex flex-col">
      {/* Nav */}
      <header className="border-b bg-card/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="container flex h-16 items-center justify-between">
          <Link to="/" className="flex items-center gap-2 font-display font-bold text-lg">
            <Sparkles className="h-5 w-5 text-primary" />
            SlideCraft AI
          </Link>
          <div className="flex items-center gap-3">
            <Link to="/history" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
              История
            </Link>
            <Button variant="outline" size="sm" onClick={handleLogout}>
              Выйти
            </Button>
          </div>
        </div>
      </header>

      <main className="flex-1 container py-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 max-w-6xl mx-auto">
          {/* Left: Form */}
          <div>
            <h1 className="text-2xl font-display font-bold mb-1">Новая презентация</h1>
            <p className="text-muted-foreground mb-6">Заполните параметры и нажмите «Сгенерировать»</p>
            <div className="mb-4">
              <DocumentUploadCard
                attachedFileName={attachedDocumentName}
                isUploading={uploadingDocument}
                disabled={loading}
                onUpload={handleDocumentUpload}
                onClear={handleDocumentClear}
              />
            </div>
            <div className="rounded-xl border bg-card p-6 shadow-card">
              <PromptForm onSubmit={handleSubmit} isLoading={loading || uploadingDocument} />
            </div>
          </div>

          {/* Right: placeholder */}
          <div className="flex items-center justify-center">
            <div className="text-center space-y-4 text-muted-foreground">
              <div className="mx-auto rounded-full bg-secondary p-6">
                <Sparkles className="h-10 w-10 text-primary animate-pulse-slow" />
              </div>
              <p className="text-sm max-w-xs mx-auto">
                После генерации здесь появится статус задачи и превью слайдов
              </p>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
