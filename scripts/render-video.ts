import fs from "fs";
import path from "path";
import { execSync } from "child_process";
import { bundle } from "@remotion/bundler";
import { renderMedia, selectComposition } from "@remotion/renderer";

async function main() {
  const args = process.argv.slice(2);
  let dayNum = 1;
  let outputPath = "output/nash_stoik_day_001_master.mp4";

  for (let i = 0; i < args.length; i++) {
    if (args[i] === "--day" && args[i + 1]) dayNum = Number(args[i + 1]);
    if (args[i] === "--out" && args[i + 1]) outputPath = args[i + 1];
  }

  const packetFile = path.resolve(`curriculum/content_packet_day_${String(dayNum).padStart(3, "0")}.json`);
  if (!fs.existsSync(packetFile)) {
    console.error(`Error: Packet file not found: ${packetFile}`);
    process.exit(1);
  }

  const packet = JSON.parse(fs.readFileSync(packetFile, "utf-8"));
  fs.mkdirSync(path.dirname(path.resolve(outputPath)), { recursive: true });

  const script = packet.script || "";
  // Use user's authentic narration if available
  const userAudio = "voiceover_user.mp3";
  const defaultAudio = `voiceover_day_${String(dayNum).padStart(3, "0")}.mp3`;
  const audioFile = fs.existsSync(path.resolve("public", userAudio)) ? userAudio : defaultAudio;
  const audioPath = path.resolve("public", audioFile);

  console.log(`[Audio] Using audio: ${audioFile} (${audioPath})`);

  // Measure audio duration via ffprobe
  let audioDuration = 50.6;
  try {
    const probe = execSync(
      `ffprobe -v error -show_entries format=duration -of csv=p=0 "${audioPath}"`,
      { encoding: "utf-8" }
    ).trim();
    audioDuration = parseFloat(probe);
    console.log(`[Audio] Durasi audio terukur: ${audioDuration.toFixed(2)} detik`);
  } catch (e) {
    console.warn(`[Audio] Warning ffprobe: ${e}, fallback to 50.6s`);
  }

  const fps = 24;
  // +1.4s cushion buffer for outro and seamless looping (Rule 48)
  const durationInFrames = Math.ceil((audioDuration + 1.4) * fps);

  // Load Timed Subtitles
  const subFile = path.resolve("curriculum/subtitles_user_001.json");
  let timedSubtitles = [];
  if (fs.existsSync(subFile)) {
    timedSubtitles = JSON.parse(fs.readFileSync(subFile, "utf-8"));
    console.log(`[Subtitles] Loaded ${timedSubtitles.length} timed subtitle cues.`);
  }

  // 5-Scene Atmospheric Human Realism Sequence (Faceless + Ethereal HyperFrames)
  const scenes = [
    {
      scene_id: "SCENE_01_NIGHT_INSOMNIA",
      timeStart: 0,
      timeEnd: 11.4,
      videoSrc: "broll/scene_01_night_insomnia.mp4",
    },
    {
      scene_id: "SCENE_02_RAIN_WINDOW",
      timeStart: 11.4,
      timeEnd: 20.7,
      videoSrc: "broll/scene_02_rain_window.mp4",
    },
    {
      scene_id: "SCENE_03_HYPERFRAMES_ETHEREAL",
      timeStart: 20.7,
      timeEnd: 36.6,
      videoSrc: "hyperframes_stoic_ethereal.mp4",
    },
    {
      scene_id: "SCENE_04_COFFEE_STEAM",
      timeStart: 36.6,
      timeEnd: 45.5,
      videoSrc: "broll/scene_04_coffee_steam.mp4",
    },
    {
      scene_id: "SCENE_05_SUNRISE_HORIZON",
      timeStart: 45.5,
      timeEnd: audioDuration + 1.4,
      videoSrc: "broll/scene_05_walking_sunrise.mp4",
    },
  ];

  const inputProps = {
    channelName: "Nash Stoik",
    channelHandle: "@nashstoik",
    title: packet.title || "Hukum Dikotomi Kendali: Rahasia Hati Baja Epictetus",
    script,
    timedSubtitles,
    audioFile,
    bgmFile: "bgm_stoic_ambient.mp3",
    scenes,
  };

  console.log(`[Remotion + HyperFrames] Bundling composition entry...`);
  const bundleLocation = await bundle({
    entryPoint: path.resolve("remotion/index.ts"),
    webpackOverride: (config) => config,
  });

  console.log(`[Remotion + HyperFrames] Selecting composition 'StoicShortsVideo'...`);
  const composition = await selectComposition({
    serveUrl: bundleLocation,
    id: "StoicShortsVideo",
    inputProps,
  });

  const CHROME =
    process.env.REMOTION_BROWSER_EXECUTABLE ||
    process.env.REMOTION_CHROMIUM_EXECUTABLE ||
    undefined;

  console.log(
    `[Remotion + HyperFrames] Rendering ${durationInFrames} frames (${(durationInFrames / fps).toFixed(1)}s) at 720x1280 @24fps to ${outputPath}...`
  );

  await renderMedia({
    composition: {
      ...composition,
      durationInFrames,
      fps: 24,
      width: 720,
      height: 1280,
    },
    serveUrl: bundleLocation,
    codec: "h264",
    imageFormat: "jpeg",
    jpegQuality: 70,
    crf: 23,
    outputLocation: path.resolve(outputPath),
    inputProps,
    browserExecutable: CHROME,
    chromiumOptions: {
      gl: "angle",
      args: [
        "--no-sandbox",
        "--disable-setuid-sandbox",
        "--use-gl=angle",
        "--use-angle=d3d11",
      ],
    },
    concurrency: 1,
    onProgress: ({ renderedFrames, encodedFrames }) => {
      const pct = Math.round((renderedFrames / durationInFrames) * 100);
      if (renderedFrames % 120 === 0 || renderedFrames === durationInFrames) {
        process.stdout.write(`\r[Remotion] Render Progress: ${pct}% (${renderedFrames}/${durationInFrames} frames)`);
      }
    },
  });

  console.log(`\n[Remotion] Master video successfully rendered to: ${outputPath}`);
}

main().catch((err) => {
  console.error("Fatal render error:", err);
  process.exit(1);
});
