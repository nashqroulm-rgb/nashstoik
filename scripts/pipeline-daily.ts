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

  console.log("=" .repeat(60));
  console.log(`  NASH STOIK AUTONOMOUS PIPELINE: DAY ${dayNum}`);
  console.log("=" .repeat(60));

  // 1. Synthesize voiceover
  console.log("\n[Tahap 1/4] Edge-TTS Voiceover Synthesis (ArdiNeural)...");
  execSync(`python scripts/generate-voiceover.py`, { stdio: "inherit" });

  // 2. Render HyperFrames Vector Scenes
  console.log("\n[Tahap 2/4] HyperFrames Vector Motion Rendering...");
  const hfScene = "hyperframes_scenes/scenes/scene_dichotomy_compass.html";
  const hfOutput = "public/hyperframes_dichotomy_compass.mp4";
  if (!fs.existsSync(hfOutput)) {
    execSync(
      `npx hyperframes render -c "${hfScene}" -o "${hfOutput}" --fps 24 --low-memory-mode`,
      { stdio: "inherit" }
    );
  } else {
    console.log(`[HyperFrames] Klip ${hfOutput} sudah tersedia, melewati render.`);
  }

  // 3. Render Remotion Composition
  console.log("\n[Tahap 3/4] Remotion Multi-Track Video Assembly...");
  execSync(`npx tsx scripts/render-video.ts --day ${dayNum}`, { stdio: "inherit" });

  // 4. Pre-Upload FFmpeg Compression (< 3.8 MB)
  console.log("\n[Tahap 4/4] Hardware / FFmpeg Pre-Upload Compression...");
  const masterMp4 = `output/nash_stoik_day_${String(dayNum).padStart(3, "0")}_master.mp4`;
  const compMp4 = `output/nash_stoik_day_${String(dayNum).padStart(3, "0")}_compressed.mp4`;
  execSync(
    `ffmpeg -y -i "${masterMp4}" -vf "scale=720:1280" -c:v libx264 -crf 34 -preset fast -c:a aac -b:a 64k "${compMp4}"`,
    { stdio: "inherit" }
  );

  console.log(`\n[Pipeline Selesai] File siap tayang: ${compMp4}`);
}

runDailyPipeline().catch((err) => {
  console.error("Pipeline failure:", err);
  process.exit(1);
});
