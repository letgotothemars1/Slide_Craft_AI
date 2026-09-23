import { useLanguage } from "@/context/LanguageContext";

interface Props {
  images: string[];
}

export default function PreviewGallery({ images }: Props) {
  const { t } = useLanguage();

  return (
    <div className="space-y-3">
      <h2 className="text-sm font-medium text-muted-foreground">{t("job.previews")}</h2>
      <ul className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {images.map((src, i) => (
          <li
            key={i}
            className="aspect-video overflow-hidden rounded-xl border border-border bg-card shadow-card"
          >
            {/* The zoom is clipped by the parent's overflow, so it magnifies
                inside the frame without pushing neighbouring cards around. */}
            <img
              src={src}
              alt={`${t("job.slideAlt")} ${i + 1}`}
              className="h-full w-full object-cover transition-transform duration-300 hover:scale-105"
              loading="lazy"
            />
          </li>
        ))}
      </ul>
    </div>
  );
}
