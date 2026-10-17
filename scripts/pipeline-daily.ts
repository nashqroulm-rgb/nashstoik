import fs from "fs";
import path from "path";
import { execSync } from "child_process";

async function runDailyPipeline() {
  const args = process.argv.slice(2);
  let dayNum = 1;

  for (let i = 0; i < args.length; i++) {
    if (args[i] === "--day" && args[i + 1]) {
      dayNum = Number(args[i + 1]);
    }
  }

  const dayStr = String(dayNum).padStart(3, "0");
  console.log("=" .repeat(64));
  console.log(`  NASH STOIK AUTONOMOUS PRODUCTION PIPELINE: DAY ${dayStr}`);
  console.log("=" .repeat(64));

  // 1. Audio Sync & Subtitle Generation
  console.log(`\n[Tahap 1/4] Audio Sync & Subtitle Timestamps (Gemini 3.8 Flash)...`);
  execSync(`python scripts/sync-audio.py ${dayNum}`, { stdio: "inherit" });

  // 2. HyperFrames Vector Scene Verification / Render
  console.log(`\n[Tahap 2/4] HyperFrames Dynamic Vector Ethereal Engine...`);
  const hfScene = "hyperframes_scenes/scenes/scene_stoic_ethereal.html";
  const hfOutput = "public/hyperframes_stoic_ethereal.mp4";
  if (!fs.existsSync(hfOutput)) {
    execSync(
      `npx hyperframes render -c "${hfScene}" -o "${hfOutput}" --fps 24 --low-memory-mode`,
      { stdio: "inherit" }
    );
  } else {
    console.log(`[HyperFrames] Klip master ${hfOutput} terverifikasi siap pakai.`);
  }

  // 3. Remotion Multi-Track Video Assembly
  console.log(`\n[Tahap 3/4] Remotion Multi-Track Compositing (Atmospheric Human Realism)...`);
  execSync(`npx tsx scripts/render-video.ts --day ${dayNum}`, { stdio: "inherit" });

  // 4. Pre-Upload FFmpeg Compression (< 3.8 MB for Zernio & Socials)
  console.log(`\n[Tahap 4/4] FFmpeg Pre-Upload Compression & Audio Equalization...`);
  const masterMp4 = `output/nash_stoik_day_${dayStr}_master.mp4`;
  const compMp4 = `output/nash_stoik_day_${dayStr}_compressed.mp4`;
  execSync(
    `ffmpeg -y -i "${masterMp4}" -vf "scale=720:1280" -c:v libx264 -crf 32 -preset fast -c:a aac -b:a 64k "${compMp4}"`,
    { stdio: "inherit" }
  );

  const sizeMb = (fs.statSync(compMp4).size / (1024 * 1024)).toFixed(2);
  console.log(`\n[PIPELINE SUKSES] Video Day ${dayStr} siap tayang: ${compMp4} (${sizeMb} MB)`);
}

runDailyPipeline().catch((err) => {
  console.error("Pipeline failure:", err);
  process.exit(1);
});
