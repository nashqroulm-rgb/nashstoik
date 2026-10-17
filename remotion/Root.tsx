import React from "react";
import { Composition } from "remotion";
import { StoicShorts } from "./components/StoicShorts";

export const Root: React.FC = () => {
  return (
    <>
      <Composition
        id="StoicShortsVideo"
        component={StoicShorts}
        durationInFrames={1296} // Default ~54s @ 24fps (dinamis di override lewat CLI)
        fps={24}
        width={720}
        height={1280}
        defaultProps={{
          channelName: "Nash Stoik",
          channelHandle: "@nashstoik",
          title: "Hukum Dikotomi Kendali",
          script:
            "Berhenti menyiksa dirimu atas hal yang tak bisa kau kendalikan! Epictetus dua ribu tahun lalu menegaskan: ada hal dalam kuasamu, dan ada hal di luar kuasamu. Opini bos, gosip rekan kerja, hasil investasi, dan masa lalu sepenuhnya di luar kendalimu. Yang seratus persen ada di tanganmu adalah pikiranmu, responmu, dan integritasmu hari ini. Setiap kali cemas melanda, tanyakan: apakah ini dalam kendaliku? Jika tidak, buang dan tenanglah.",
          audioFile: "voiceover_day_001.mp3",
          bgmFile: "bgm_stoic_ambient.mp3",
          scenes: [],
        }}
      />
    </>
  );
};
