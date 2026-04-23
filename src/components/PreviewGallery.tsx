interface Props {
  images: string[];
}

export default function PreviewGallery({ images }: Props) {
  return (
    <div className="space-y-3">
      <h3 className="text-sm font-medium text-muted-foreground">Превью слайдов</h3>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
        {images.map((src, i) => (
          <div key={i} className="overflow-hidden rounded-lg border bg-card shadow-card aspect-video">
            <img
              src={src}
              alt={`Слайд ${i + 1}`}
              className="h-full w-full object-cover transition-transform hover:scale-105"
              loading="lazy"
            />
          </div>
        ))}
      </div>
    </div>
  );
}
