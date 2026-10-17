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
  console.log(`  NASH STOIK PRODUCTION PIPELINE: DAY ${dayStr}`);
  console.log("=" .repeat(64));

  // Run the calibrated high-speed production pipeline (FFmpeg + Ethereal HyperFrames)
  console.log(`\n[Rendering Day ${dayStr}] Assembling 5-scene faceless B-roll, HyperFrames, and subtitles...`);
  execSync(`python scripts/render-fast.py ${dayNum}`, { stdio: "inherit" });

  const compMp4 = `output/nash_stoik_day_${dayStr}_compressed.mp4`;
  if (fs.existsSync(compMp4)) {
    const sizeMb = (fs.statSync(compMp4).size / (1024 * 1024)).toFixed(2);
    console.log(`\n[SUKSES] Video Day ${dayStr} siap tayang: ${compMp4} (${sizeMb} MB)`);
  }
}

runDailyPipeline().catch((err) => {
  console.error("Pipeline failure:", err);
  process.exit(1);
});
