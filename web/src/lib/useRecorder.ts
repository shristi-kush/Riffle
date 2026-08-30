import { useCallback, useRef, useState } from "react";

interface Options {
  /** Called with the captured audio once recording stops. */
  onComplete: (audio: Blob, filename: string) => void;
}

function recorderOptions(): MediaRecorderOptions {
  const options: MediaRecorderOptions = { audioBitsPerSecond: 128_000 };
  for (const mime of ["audio/webm;codecs=opus", "audio/webm", "audio/ogg;codecs=opus"]) {
    if (typeof MediaRecorder !== "undefined" && MediaRecorder.isTypeSupported(mime)) {
      options.mimeType = mime;
      break;
    }
  }
  return options;
}

/** Browser microphone capture via MediaRecorder. */
export function useRecorder({ onComplete }: Options) {
  const [recording, setRecording] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const recorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<BlobPart[]>([]);

  const start = useCallback(async () => {
    setError(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
          channelCount: 1,
          sampleRate: 16000,
        },
      });
      const recorder = new MediaRecorder(stream, recorderOptions());
      chunksRef.current = [];

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };
      recorder.onstop = () => {
        const type = recorder.mimeType || "audio/webm";
        const ext = type.includes("ogg") ? "ogg" : type.includes("wav") ? "wav" : "webm";
        const blob = new Blob(chunksRef.current, { type });
        stream.getTracks().forEach((t) => t.stop());
        onComplete(blob, `question.${ext}`);
      };

      recorder.start(100);
      recorderRef.current = recorder;
      setRecording(true);
    } catch {
      setError("Microphone access was denied. Upload an audio file instead.");
    }
  }, [onComplete]);

  const stop = useCallback(() => {
    recorderRef.current?.stop();
    recorderRef.current = null;
    setRecording(false);
  }, []);

  const toggle = useCallback(() => {
    if (recording) stop();
    else void start();
  }, [recording, start, stop]);

  return { recording, error, toggle, start, stop };
}
