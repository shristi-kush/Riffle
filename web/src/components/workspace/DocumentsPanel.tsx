import { useCallback, useEffect, useRef, useState } from "react";
import { fetchCorpus, ingestPdf, type CorpusDocument } from "../../lib/api";
import { DocIcon } from "../icons";

interface Props {
  onAudioFile: (audio: Blob, filename: string) => void;
  onCorpusChange?: (count: number) => void;
  recorderError?: string | null;
  busy?: boolean;
  sessionKey?: number;
}

export default function DocumentsPanel({
  onAudioFile,
  onCorpusChange,
  recorderError,
  busy,
  sessionKey = 0,
}: Props) {
  const [docs, setDocs] = useState<CorpusDocument[]>([]);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [dragging, setDragging] = useState(false);
  const audioRef = useRef<HTMLInputElement>(null);

  const loadCorpus = useCallback(async () => {
    try {
      const next = await fetchCorpus();
      setDocs(next);
      onCorpusChange?.(next.length);
    } catch {
      setDocs([]);
      onCorpusChange?.(0);
    }
  }, [onCorpusChange]);

  useEffect(() => {
    setDocs([]);
    onCorpusChange?.(0);
    void loadCorpus();
  }, [loadCorpus, sessionKey, onCorpusChange]);

  const upload = async (file: File) => {
    if (!file.name.toLowerCase().endsWith(".pdf")) {
      setError("Only PDF files are supported.");
      return;
    }
    setUploading(true);
    setError(null);
    try {
      await ingestPdf(file);
      await loadCorpus();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ingest failed.");
    } finally {
      setUploading(false);
    }
  };

  return (
    <section>
      <h2 className="mb-3 flex items-center gap-2 text-h4">
        <DocIcon className="h-4 w-4 text-cyan-accent" />
        Documents
      </h2>

      <label
        onDragOver={(e) => {
          e.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragging(false);
          const file = e.dataTransfer.files?.[0];
          if (file) void upload(file);
        }}
        className={`flex cursor-pointer flex-col items-center justify-center gap-1 rounded-xl border border-dashed px-4 py-6 text-center transition ${
          dragging
            ? "border-cyan-accent bg-cyan-accent/10"
            : "border-white/12 bg-white/[0.02] hover:border-cyan-accent/50 hover:bg-white/[0.04]"
        }`}
      >
        <input
          type="file"
          accept="application/pdf"
          className="hidden"
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) void upload(file);
            e.target.value = "";
          }}
        />
        {uploading ? (
          <span className="text-small text-cyan-accent">Indexing...</span>
        ) : (
          <>
            <span className="text-small text-text-med">Drop a PDF here</span>
            <span className="text-[13px] text-text-low">or click to browse</span>
          </>
        )}
      </label>

      {docs.length > 0 && (
        <ul className="mt-3 space-y-2">
          {docs.map((doc) => (
            <li
              key={doc.filename}
              className="rounded-xl border border-success/25 bg-success/10 px-3 py-2 text-[13px] text-success"
            >
              <p className="truncate font-medium">{doc.filename}</p>
              <p className="font-mono text-[11px] opacity-80">
                {doc.chunks} chunks · {doc.pages} pages
              </p>
            </li>
          ))}
        </ul>
      )}

      {error && (
        <div className="mt-3 rounded-xl border border-danger/25 bg-danger/10 px-3 py-2 text-[13px] text-danger">
          {error}
        </div>
      )}

      <div className="mt-5">
        <h3 className="eyebrow mb-2 text-text-low">Voice fallback</h3>
        <button
          onClick={() => audioRef.current?.click()}
          disabled={busy}
          className="w-full rounded-xl border border-white/10 bg-white/[0.03] px-4 py-2 text-small text-text-med transition hover:border-white/20 hover:text-text-high disabled:cursor-not-allowed disabled:opacity-40"
        >
          Upload audio question
        </button>
        <input
          ref={audioRef}
          type="file"
          accept="audio/*"
          className="hidden"
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) onAudioFile(file, file.name);
            e.target.value = "";
          }}
        />
        {recorderError && (
          <p className="mt-2 text-[13px] text-danger">{recorderError}</p>
        )}
      </div>
    </section>
  );
}
