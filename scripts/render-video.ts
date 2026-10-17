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
  const audioFile = `voiceover_day_${String(dayNum).padStart(3, "0")}.mp3`;
  const audioPath = path.resolve("public", audioFile);

  if (!fs.existsSync(audioPath)) {
    console.log(`[Audio] File ${audioFile} belum ada. Menjalankan scripts/generate-voiceover.py...`);
    execSync(`python scripts/generate-voiceover.py`, { stdio: "inherit" });
  }

  // Ukur durasi audio riil via ffprobe (Rule 1: Dynamic Duration Invariant)
  let audioDuration = 45;
  try {
    const probe = execSync(
      `ffprobe -v error -show_entries format=duration -of csv=p=0 "${audioPath}"`,
      { encoding: "utf-8" }
    ).trim();
    audioDuration = parseFloat(probe);
    console.log(`[Audio] Durasi audio terukur: ${audioDuration.toFixed(2)} detik`);
  } catch (e) {
    console.warn(`[Audio] Warning ffprobe: ${e}, fallback to 45s`);
  }

  const fps = 24;
  // +1.5s cushion buffer for outro (Rule 45)
  const durationInFrames = Math.ceil((audioDuration + 1.5) * fps);

  // HyperFrames clip sequence
  const scenes = [
    {
      scene_id: "SCENE_01_HYPERFRAMES_COMPASS",
      timeStart: 0,
      timeEnd: audioDuration + 1.5,
      videoSrc: "hyperframes_dichotomy_compass.mp4",
    },
  ];

  const inputProps = {
    channelName: "Nash Stoik",
    channelHandle: "@nashstoik",
    title: packet.title || "Hukum Dikotomi Kendali: Rahasia Hati Baja Epictetus",
    script,
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
        "--enable-gpu-rasterization",
      ],
    } as any,
    concurrency: 4,
    onProgress: ({ progress }) => {
      process.stdout.write(`\r[Remotion] Progress: ${(progress * 100).toFixed(0)}%`);
    },
  });

  console.log(`\n[Remotion] Render complete -> ${outputPath}`);
  const stat = fs.statSync(outputPath);
  console.log(`[Remotion] Final MP4 Size: ${(stat.size / (1024 * 1024)).toFixed(2)} MB`);
}

main().catch((err) => {
  console.error("[Remotion] Error:", err);
  process.exit(1);
});
