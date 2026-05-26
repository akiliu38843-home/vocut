import { Config } from "@remotion/cli/config";

Config.setVideoImageFormat("jpeg");
Config.setOverwriteOutput(true);
Config.setPixelFormat("yuv420p");
Config.setCodec("h264");

// CardBackground shader bg_style runs an actual WebGL fragment shader via
// @remotion/three. Headless Chromium needs an explicit GL renderer for this;
// "angle" is the fastest deterministic backend that works in CI.
Config.setChromiumOpenGlRenderer("angle");
