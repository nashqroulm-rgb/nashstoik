
import path from "path";
import { bundle } from "@remotion/bundler";
import { renderMedia, selectComposition } from "@remotion/renderer";

async function test() {
  const bundleLocation = await bundle({
    entryPoint: path.resolve("remotion/index.ts"),
  });
  const composition = await selectComposition({
    serveUrl: bundleLocation,
    id: "StoicShortsVideo",
    inputProps: {
      audioFile: "voiceover_user.mp3",
      timedSubtitles: [],
      scenes: []
    }
  });
  console.log("Starting 120-frame (5s) test render...");
  const t0 = Date.now();
  await renderMedia({
    composition: { ...composition, durationInFrames: 120, fps: 24, width: 720, height: 1280 },
    serveUrl: bundleLocation,
    codec: "h264",
    outputLocation: path.resolve("output/test_5s.mp4"),
    concurrency: 2,
  });
  console.log("Rendered 120 frames in " + ((Date.now() - t0)/1000).toFixed(1) + "s");
}
test();
