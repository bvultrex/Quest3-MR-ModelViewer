from pathlib import Path
import re

source_path = Path('meta-openxr-sdk/Samples/XrSamples/XrPassthroughOcclusion/Src/XrPassthroughOcclusionGl.cpp')
text = source_path.read_text()

hard_occlusion = re.compile(
    r"outColor\s*=\s*fragmentColor;\s*"
    r"if\s*\(cubeDepth\s*<\s*depthViewEyeZ\)\s*\{\s*"
    r"outColor\.a\s*=\s*1\.0f;[^\n]*\s*"
    r"\}\s*else\s*\{\s*"
    r"outColor\s*=\s*vec4\(0\.0f,\s*0\.0f,\s*0\.0f,\s*0\.0f\);[^\n]*\s*"
    r"\}\s*",
    re.S,
)

filtered_occlusion = "\n".join([
    "// Quest3 MR Model Viewer v0.1.2 filtered Environment Depth pass",
    "// Estimate fractional occlusion coverage from a 3x3 neighbourhood instead of",
    "// trusting a single low-resolution Environment Depth texel.",
    "highp ivec3 depthTextureSize3 = textureSize(EnvironmentDepthTexture, 0);",
    "highp vec2 depthTexel = 1.0f / vec2(depthTextureSize3.xy);",
    "",
    "// clip.w is a useful distance hint in this perspective projection. Increase",
    "// the conservative bias slightly with distance, where one depth texel covers",
    "// more world-space area.",
    "highp float distanceHint = max(abs(cubeDepthCameraPosition.w), 0.25f);",
    "highp float projectedBias = clamp(0.00022f + distanceHint * 0.00016f, 0.00022f, 0.00120f);",
    "",
    "// Sub-pixel depth-space feather for quantisation and reprojection jitter.",
    "highp float derivativeWidth = clamp(fwidth(cubeDepth) * 1.35f, 0.00030f, 0.00250f);",
    "",
    "highp float visibilitySum = 0.0f;",
    "highp float weightSum = 0.0f;",
    "",
    "for (int y = -1; y <= 1; ++y) {",
    "    for (int x = -1; x <= 1; ++x) {",
    "        highp vec2 tapUv = clamp(",
    "            cubeDepthCameraPositionHC + vec2(float(x), float(y)) * depthTexel,",
    "            vec2(0.0f),",
    "            vec2(1.0f));",
    "",
    "        highp float realDepth = texture(",
    "            EnvironmentDepthTexture,",
    "            vec3(tapUv, float(VIEW_ID))).r;",
    "",
    "        // Gaussian kernel: 1 2 1 / 2 4 2 / 1 2 1, total 16.",
    "        highp float wx = (x == 0) ? 2.0f : 1.0f;",
    "        highp float wy = (y == 0) ? 2.0f : 1.0f;",
    "        highp float weight = wx * wy;",
    "",
    "        // Positive delta means virtual geometry is in front of the real sample.",
    "        // Bias toward the real world to reduce virtual leaks at depth edges.",
    "        highp float depthDelta = realDepth - cubeDepth - projectedBias;",
    "",
    "        // Expand the feather only around depth discontinuities, where the raw",
    "        // mask is most likely to show stair-stepping or temporal shimmer.",
    "        highp float discontinuity = abs(realDepth - depthViewEyeZ);",
    "        highp float tapWidth = clamp(",
    "            derivativeWidth + discontinuity * 0.12f,",
    "            0.00040f,",
    "            0.00450f);",
    "",
    "        highp float tapVisibility = smoothstep(-tapWidth, tapWidth, depthDelta);",
    "        visibilitySum += tapVisibility * weight;",
    "        weightSum += weight;",
    "    }",
    "}",
    "",
    "highp float visibility = clamp(visibilitySum / max(weightSum, 0.0001f), 0.0f, 1.0f);",
    "",
    "// Tighten the transition to avoid a broad translucent halo while preserving",
    "// fractional edge coverage.",
    "visibility = smoothstep(0.08f, 0.92f, visibility);",
    "outColor = vec4(fragmentColor.rgb, fragmentColor.a * visibility);",
    "",
])

text, count = hard_occlusion.subn(filtered_occlusion, text, count=1)
if count != 1:
    raise SystemExit(f'Expected one hard occlusion block, patched {count}')

renderer_create = re.compile(
    r"EglInitExtensions\(\);\s*"
    r"if\s*\(!framebuffer\.Create\(\s*"
    r"format,\s*width,\s*height,\s*numMultiSamples,\s*swapChainLength,\s*colorTextures\)\)\s*\{",
    re.S,
)

msaa_block = "\n".join([
    "EglInitExtensions();",
    "",
    "    GLint maxSamples = 1;",
    "    GL(glGetIntegerv(GL_MAX_SAMPLES, &maxSamples));",
    "    const int qualitySamples = (maxSamples >= 4) ? 4 : ((maxSamples >= 2) ? 2 : 1);",
    "    const int selectedSamples = glExtensions.multi_view ? qualitySamples : 1;",
    "    ALOGV(",
    "        \"Quest3 MR v0.1.2: %dx MSAA selected (runtime requested %d, GL max %d)\",",
    "        selectedSamples,",
    "        numMultiSamples,",
    "        maxSamples);",
    "",
    "    if (!framebuffer.Create(",
    "            format, width, height, selectedSamples, swapChainLength, colorTextures)) {",
])

text, count = renderer_create.subn(msaa_block, text, count=1)
if count != 1:
    raise SystemExit(f'Expected one AppRenderer::Create block, patched {count}')

render_state = re.compile(
    r"GL\(glDisable\(GL_BLEND\)\);\s*"
    r"GL\(glBlendFunc\(GL_SRC_ALPHA,\s*GL_ONE_MINUS_SRC_ALPHA\)\);",
    re.S,
)
coverage_state = "\n".join([
    "GL(glDisable(GL_BLEND));",
    "    GL(glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA));",
    "    GL(glEnable(GL_SAMPLE_ALPHA_TO_COVERAGE));",
])
text, count = render_state.subn(coverage_state, text, count=1)
if count != 1:
    raise SystemExit(f'Expected one RenderScene blend state block, patched {count}')

source_path.write_text(text)
print('3x3 Gaussian Environment Depth coverage: ON')
print('Distance-adaptive conservative bias: ON')
print('Discontinuity-aware feather: ON')
print('MSAA alpha-to-coverage: ON')
print('MSAA preference: 4x -> 2x -> 1x fallback')
