import React from "react";
import {
  AbsoluteFill,
  Audio,
  Video,
  Sequence,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  spring,
} from "remotion";

export interface StoicSceneItem {
  scene_id?: string;
  timeStart: number;
  timeEnd: number;
  videoSrc: string;
}

export interface StoicShortsProps {
  channelName?: string;
  channelHandle?: string;
  title?: string;
  script: string;
  audioFile?: string;
  bgmFile?: string;
  scenes?: StoicSceneItem[];
}

function chunkWords(text: string, maxWords = 4): string[] {
  const words = text.split(/\s+/).filter(Boolean);
  const out: string[] = [];
  for (let i = 0; i < words.length; i += maxWords) {
    out.push(words.slice(i, i + maxWords).join(" "));
  }
  return out;
}

export const StoicShorts: React.FC<StoicShortsProps> = ({
  channelName = "Nash Stoik",
  channelHandle = "@nashstoik",
  title = "Dikotomi Kendali: Rahasia Hati Baja",
  script,
  audioFile = "voiceover_day_001.mp3",
  bgmFile = "bgm_stoic_ambient.mp3",
  scenes = [],
}) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();

  // Progress Bar
  const totalProgress = frame / durationInFrames;

  // Subtitle synchronization
  const lines = chunkWords(script);
  const lineDuration = Math.max(1, Math.floor(durationInFrames / Math.max(lines.length, 1)));
  const lineIndex = Math.min(lines.length - 1, Math.floor(frame / lineDuration));
  const currentLine = lines[lineIndex] || "";
  const progressInLine = (frame % lineDuration) / lineDuration;

  // Kinetic subtitle spring animation
  const textScale = spring({
    frame: frame % lineDuration,
    fps,
    config: { damping: 14, stiffness: 130 },
  });

  const textOpacity = interpolate(progressInLine, [0, 0.1, 0.9, 1], [0.4, 1, 1, 0.5], {
    extrapolateRight: "clamp",
    extrapolateLeft: "clamp",
  });

  // Background subtle breathing zoom
  const bgScale = interpolate(frame, [0, durationInFrames], [1, 1.05], {
    extrapolateRight: "clamp",
  });

  // Hook Banner Opacity (first 4.5 seconds)
  const hookBannerOpacity = interpolate(frame, [0, fps * 3.8, fps * 4.8], [1, 1, 0], {
    extrapolateRight: "clamp",
  });

  // Outro Card (final 3.5 seconds)
  const outroStartFrame = durationInFrames - Math.round(fps * 3.5);
  const outroOpacity = interpolate(frame, [outroStartFrame, outroStartFrame + 15], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill
      style={{
        backgroundColor: "#030712",
        color: "#f9fafb",
        fontFamily: "'Segoe UI', Roboto, 'Georgia', serif",
        overflow: "hidden",
      }}
    >
      {/* 1. Voiceover Audio & Ducked BGM */}
      <Audio src={staticFile(audioFile)} />
      <Audio src={staticFile(bgmFile)} volume={0.14} />

      {/* 2. Video Track: B-Roll + HyperFrames Sequences */}
      <AbsoluteFill style={{ transform: `scale(${bgScale})` }}>
        {scenes && scenes.length > 0 ? (
          scenes.map((sc, idx) => {
            const startFrame = Math.round((sc.timeStart || 0) * fps);
            const endFrame = Math.round((sc.timeEnd || durationInFrames / fps) * fps);
            const duration = Math.max(1, endFrame - startFrame);

            return (
              <Sequence
                key={`${sc.scene_id || idx}-${startFrame}`}
                from={startFrame}
                durationInFrames={duration}
              >
                <Video
                  src={staticFile(sc.videoSrc)}
                  muted
                  style={{
                    width: "100%",
                    height: "100%",
                    objectFit: "cover",
                  }}
                />
              </Sequence>
            );
          })
        ) : (
          <div
            style={{
              width: "100%",
              height: "100%",
              background: "linear-gradient(180deg, #1f2937 0%, #030712 100%)",
            }}
          />
        )}
      </AbsoluteFill>

      {/* 3. Aesthetic Dark Vignette Overlay for Crisp Subtitle Readability */}
      <AbsoluteFill
        style={{
          background:
            "linear-gradient(180deg, rgba(3, 7, 18, 0.75) 0%, rgba(3, 7, 18, 0.15) 30%, rgba(3, 7, 18, 0.3) 65%, rgba(3, 7, 18, 0.92) 100%)",
          pointerEvents: "none",
        }}
      />

      {/* 4. Top Header Branding Badge (Always Visible & Elegant) */}
      <div
        style={{
          position: "absolute",
          top: 45,
          left: 0,
          right: 0,
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          zIndex: 40,
        }}
      >
        <div
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: 10,
            background: "rgba(10, 15, 23, 0.85)",
            border: "1px solid rgba(212, 175, 55, 0.4)",
            borderRadius: 9999,
            padding: "8px 22px",
            boxShadow: "0 8px 30px rgba(0, 0, 0, 0.6)",
            backdropFilter: "blur(10px)",
          }}
        >
          <div
            style={{
              width: 8,
              height: 8,
              borderRadius: "50%",
              backgroundColor: "#d4af37",
              boxShadow: "0 0 10px #d4af37",
            }}
          />
          <span
            style={{
              fontSize: 13,
              fontWeight: 700,
              letterSpacing: 2.5,
              textTransform: "uppercase",
              color: "#e2e8f0",
            }}
          >
            {channelName} • FILOSOFI STOIK
          </span>
        </div>
      </div>

      {/* 5. Kinetic Subtitle Display (Positioned in Bottom Safe Zone) */}
      <div
        style={{
          position: "absolute",
          bottom: 155,
          left: 40,
          right: 40,
          textAlign: "center",
          zIndex: 50,
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
        }}
      >
        <div
          style={{
            transform: `scale(${textScale})`,
            opacity: textOpacity,
            maxWidth: 620,
          }}
        >
          <div
            style={{
              fontSize: 34,
              fontFamily: "'Impact', 'Montserrat', sans-serif",
              fontWeight: 900,
              color: "#ffffff",
              textTransform: "uppercase",
              letterSpacing: 1.5,
              lineHeight: 1.25,
              textShadow:
                "0 4px 18px rgba(0, 0, 0, 0.95), 0 0 12px rgba(0, 0, 0, 0.8), -2px -2px 0 #000, 2px -2px 0 #000, -2px 2px 0 #000, 2px 2px 0 #000",
            }}
          >
            {currentLine.split(" ").map((w, i) => {
              const isHighlight =
                w.toLowerCase().includes("kendali") ||
                w.toLowerCase().includes("cemas") ||
                w.toLowerCase().includes("tenang") ||
                w.toLowerCase().includes("pikiran") ||
                w.toLowerCase().includes("respon") ||
                w.toLowerCase().includes("fokus") ||
                w.toLowerCase().includes("stoik") ||
                w.toLowerCase().includes("baja");

              return (
                <span
                  key={i}
                  style={{
                    color: isHighlight ? "#fef08a" : "#ffffff",
                    display: "inline-block",
                    marginRight: 8,
                  }}
                >
                  {w}
                </span>
              );
            })}
          </div>
        </div>
      </div>

      {/* 7. Outro Card (Final 3.5 seconds) */}
      {outroOpacity > 0 && (
        <AbsoluteFill
          style={{
            opacity: outroOpacity,
            backgroundColor: "rgba(3, 7, 18, 0.92)",
            zIndex: 60,
            display: "flex",
            flexDirection: "column",
            justifyContent: "center",
            alignItems: "center",
            textAlign: "center",
            padding: 40,
          }}
        >
          <div
            style={{
              width: 90,
              height: 90,
              borderRadius: "50%",
              border: "2px solid #d4af37",
              boxShadow: "0 0 25px rgba(212, 175, 55, 0.5)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: 42,
              marginBottom: 18,
              background: "rgba(17, 24, 39, 0.8)",
            }}
          >
            🏛️
          </div>
          <div
            style={{
              fontSize: 26,
              fontWeight: 800,
              color: "#ffffff",
              letterSpacing: 1.5,
              marginBottom: 6,
            }}
          >
            {channelName}
          </div>
          <div
            style={{
              fontSize: 14,
              fontWeight: 600,
              color: "#d4af37",
              letterSpacing: 2,
              marginBottom: 24,
            }}
          >
            {channelHandle}
          </div>
          <div
            style={{
              fontSize: 15,
              color: "#9ca3af",
              lineHeight: 1.5,
              maxWidth: 480,
              marginBottom: 28,
            }}
          >
            Kuasai pikiranmu sebelum dunia luar menguasai hidupmu. Bagikan video ini dan ikuti untuk ketahanan mental setiap hari.
          </div>
          <div
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: 12,
              background: "#d4af37",
              color: "#030712",
              padding: "12px 28px",
              borderRadius: 9999,
              fontWeight: 800,
              fontSize: 14,
              letterSpacing: 1,
              boxShadow: "0 8px 24px rgba(212, 175, 55, 0.4)",
            }}
          >
            <span>IKUTI KELUARGA STOIK</span>
            <span>🔔</span>
          </div>
        </AbsoluteFill>
      )}

      {/* 8. Top Subtle Video Progress Bar */}
      <div
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          height: 3,
          width: `${totalProgress * 100}%`,
          backgroundColor: "#d4af37",
          zIndex: 70,
        }}
      />
    </AbsoluteFill>
  );
};
