import React from "react";
import {
  AbsoluteFill,
  Audio,
  interpolate,
  Sequence,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
  Video,
} from "remotion";

export interface StoicSceneItem {
  scene_id?: string;
  timeStart: number;
  timeEnd: number;
  videoSrc: string;
}

export interface TimedSubtitle {
  start: number;
  end: number;
  text: string;
}

export interface StoicShortsProps {
  channelName?: string;
  channelHandle?: string;
  title?: string;
  script?: string;
  timedSubtitles?: TimedSubtitle[];
  audioFile?: string;
  bgmFile?: string;
  scenes?: StoicSceneItem[];
}

const HIGHLIGHT_WORDS = [
  "kendali",
  "beban",
  "lepaskan",
  "tanganmu",
  "respon",
  "ombak",
  "perahumu",
  "tenang",
  "kuasamu",
  "tugasmu",
  "sesak",
  "lelah",
  "fokuskan",
];

const SceneRenderer: React.FC<{
  sc: StoicSceneItem;
  duration: number;
  isFirst: boolean;
}> = ({ sc, duration, isFirst }) => {
  const relFrame = useCurrentFrame();

  // Smooth Ken Burns slow zoom (Rule 20)
  const sceneScale = interpolate(relFrame, [0, duration], [1.02, 1.16], {
    extrapolateRight: "clamp",
  });

  // Slow subtle parallax drift
  const panX = interpolate(relFrame, [0, duration], [0, isFirst ? 14 : -10], {
    extrapolateRight: "clamp",
  });
  const panY = interpolate(relFrame, [0, duration], [0, -8], {
    extrapolateRight: "clamp",
  });

  // Crossfade opacity on entry & exit
  const fade = 14;
  const sceneOpacity = interpolate(
    relFrame,
    [0, fade, duration - fade, duration],
    [isFirst ? 0 : 0.3, 1, 1, 0.4],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  return (
    <AbsoluteFill style={{ overflow: "hidden" }}>
      <AbsoluteFill
        style={{
          transform: `scale(${sceneScale}) translate(${panX}px, ${panY}px)`,
          opacity: sceneOpacity,
        }}
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
      </AbsoluteFill>

      {/* Atmospheric Candlelight Glow & Organic Pulse (Only for Scene 1 - Insomnia) */}
      {isFirst && (
        <div
          style={{
            position: "absolute",
            bottom: "26%",
            right: "20%",
            width: 360,
            height: 360,
            borderRadius: "50%",
            background:
              "radial-gradient(circle, rgba(245, 158, 11, 0.35) 0%, rgba(217, 119, 6, 0.15) 45%, transparent 75%)",
            filter: "blur(40px)",
            opacity:
              0.65 +
              Math.sin(relFrame * 0.15) * 0.18 +
              Math.cos(relFrame * 0.36) * 0.08,
            pointerEvents: "none",
            mixBlendMode: "screen",
          }}
        />
      )}
    </AbsoluteFill>
  );
};

export const StoicShorts: React.FC<StoicShortsProps> = ({
  channelName = "Nash Stoik",
  channelHandle = "@nashstoik",
  title = "Dikotomi Kendali",
  script = "",
  timedSubtitles = [],
  audioFile = "voiceover_user.mp3",
  bgmFile = "bgm_stoic_ambient.mp3",
  scenes = [],
}) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();
  const currentTimeSec = frame / fps;

  // Global Progress
  const totalProgress = frame / durationInFrames;

  // Active Subtitle from Timestamps
  let currentSubtitle = "";
  let subRelFrame = 0;
  if (timedSubtitles && timedSubtitles.length > 0) {
    const active = timedSubtitles.find(
      (s) => currentTimeSec >= s.start && currentTimeSec <= s.end + 0.15
    );
    if (active) {
      currentSubtitle = active.text;
      const subStartFrame = Math.round(active.start * fps);
      subRelFrame = frame - subStartFrame;
    }
  }

  // Kinetic subtitle spring pop
  const textScale = spring({
    frame: Math.max(0, subRelFrame),
    fps,
    config: { damping: 14, stiffness: 140 },
  });

  // Outro Subtle Branding (Last 3.2s)
  const outroStartFrame = durationInFrames - Math.round(fps * 3.2);
  const outroOpacity = interpolate(
    frame,
    [outroStartFrame, outroStartFrame + 18],
    [0, 1],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  return (
    <AbsoluteFill
      style={{
        backgroundColor: "#020408",
        color: "#f8fafc",
        fontFamily: "'Segoe UI', Roboto, 'Georgia', serif",
        overflow: "hidden",
      }}
    >
      {/* 1. Voiceover (User Recording) + Ducked Ambient BGM */}
      <Audio src={staticFile(audioFile)} />
      <Audio src={staticFile(bgmFile)} volume={0.11} />

      {/* 2. Video Sequences (Ken Burns + Candle Pulse + Smooth Crossfades) */}
      <AbsoluteFill>
        {scenes && scenes.length > 0 ? (
          scenes.map((sc, idx) => {
            const startFrame = Math.round((sc.timeStart || 0) * fps);
            const endFrame = Math.round(
              (sc.timeEnd || durationInFrames / fps) * fps
            );
            const duration = Math.max(1, endFrame - startFrame);

            return (
              <Sequence
                key={`${sc.scene_id || idx}-${startFrame}`}
                from={startFrame}
                durationInFrames={duration}
              >
                <SceneRenderer
                  sc={sc}
                  duration={duration}
                  isFirst={idx === 0}
                />
              </Sequence>
            );
          })
        ) : (
          <div
            style={{
              width: "100%",
              height: "100%",
              background: "#020408",
            }}
          />
        )}
      </AbsoluteFill>

      {/* 3. Deep Cinematic Vignette (Preserves Contrast & Readability) */}
      <AbsoluteFill
        style={{
          background:
            "linear-gradient(180deg, rgba(2, 4, 8, 0.72) 0%, rgba(2, 4, 8, 0.1) 28%, rgba(2, 4, 8, 0.25) 65%, rgba(2, 4, 8, 0.88) 100%)",
          pointerEvents: "none",
        }}
      />

      {/* 4. Top Header Minimalist Badge */}
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
            background: "rgba(6, 10, 18, 0.85)",
            border: "1px solid rgba(212, 175, 55, 0.45)",
            borderRadius: 9999,
            padding: "8px 22px",
            boxShadow: "0 8px 30px rgba(0, 0, 0, 0.7)",
            backdropFilter: "blur(12px)",
          }}
        >
          <div
            style={{
              width: 7,
              height: 7,
              borderRadius: "50%",
              backgroundColor: "#fef08a",
              boxShadow: "0 0 10px #fef08a",
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

      {/* 5. Kinetic Subtitles (Synchronized to User Audio Timestamps) */}
      {currentSubtitle && (
        <div
          style={{
            position: "absolute",
            bottom: 140,
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
              maxWidth: 640,
            }}
          >
            <div
              style={{
                fontSize: 32,
                fontFamily: "'Impact', 'Montserrat', -apple-system, sans-serif",
                fontWeight: 900,
                color: "#ffffff",
                textTransform: "uppercase",
                letterSpacing: 1.4,
                lineHeight: 1.3,
                textShadow:
                  "0 4px 18px rgba(0, 0, 0, 0.95), 0 0 12px rgba(0, 0, 0, 0.8), -2px -2px 0 #000, 2px -2px 0 #000, -2px 2px 0 #000, 2px 2px 0 #000",
              }}
            >
              {currentSubtitle.split(" ").map((w, i) => {
                const cleanWord = w.toLowerCase().replace(/[^a-z0-9]/g, "");
                const isHighlight = HIGHLIGHT_WORDS.some((kw) =>
                  cleanWord.includes(kw)
                );

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
      )}

      {/* 6. Subtle Outro Horizon Seal (Final 3.2s) */}
      {outroOpacity > 0 && (
        <div
          style={{
            position: "absolute",
            bottom: 220,
            left: 0,
            right: 0,
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            opacity: outroOpacity,
            zIndex: 45,
            pointerEvents: "none",
          }}
        >
          <div
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: 12,
              background: "rgba(10, 15, 24, 0.88)",
              border: "1.5px solid rgba(212, 175, 55, 0.6)",
              borderRadius: 9999,
              padding: "10px 26px",
              boxShadow: "0 10px 35px rgba(0, 0, 0, 0.8)",
            }}
          >
            <span style={{ fontSize: 18 }}>🏛️</span>
            <span
              style={{
                fontSize: 14,
                fontWeight: 800,
                letterSpacing: 2,
                color: "#fef08a",
                textTransform: "uppercase",
              }}
            >
              {channelHandle}
            </span>
          </div>
        </div>
      )}

      {/* 7. Top Video Progress Bar */}
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
