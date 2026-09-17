from pathlib import Path
import re

source_path = Path('meta-openxr-sdk/Samples/XrSamples/XrPassthroughOcclusion/Src/XrPassthroughOcclusionGl.cpp')
text = source_path.read_text()

if '#include <algorithm>' not in text:
    text = text.replace('#include <cmath>\n', '#include <cmath>\n#include <algorithm>\n', 1)

enum_old = """        DEPTH_VIEW_MATRICES,
        DEPTH_PROJECTION_MATRICES,
    };"""
enum_new = """        DEPTH_VIEW_MATRICES,
        DEPTH_PROJECTION_MATRICES,
        LIGHT_DIRECTION,
        LIGHT_TINT,
        AMBIENT_STRENGTH,
        KEY_INTENSITY,
        EXPOSURE,
        UI_MODE,
        UI_COLOR,
    };"""
if enum_old not in text:
    raise SystemExit('Uniform enum anchor not found')
text = text.replace(enum_old, enum_new, 1)

uniforms_old = """    {Uniform::Index::DEPTH_VIEW_MATRICES, Uniform::Type::UNIFORM, \"DepthViewMatrix\"},
    {Uniform::Index::DEPTH_PROJECTION_MATRICES, Uniform::Type::UNIFORM, \"DepthProjectionMatrix\"},
};"""
uniforms_new = """    {Uniform::Index::DEPTH_VIEW_MATRICES, Uniform::Type::UNIFORM, \"DepthViewMatrix\"},
    {Uniform::Index::DEPTH_PROJECTION_MATRICES, Uniform::Type::UNIFORM, \"DepthProjectionMatrix\"},
    {Uniform::Index::LIGHT_DIRECTION, Uniform::Type::UNIFORM, \"LightDirection\"},
    {Uniform::Index::LIGHT_TINT, Uniform::Type::UNIFORM, \"LightTint\"},
    {Uniform::Index::AMBIENT_STRENGTH, Uniform::Type::UNIFORM, \"AmbientStrength\"},
    {Uniform::Index::KEY_INTENSITY, Uniform::Type::UNIFORM, \"KeyIntensity\"},
    {Uniform::Index::EXPOSURE, Uniform::Type::UNIFORM, \"Exposure\"},
    {Uniform::Index::UI_MODE, Uniform::Type::UNIFORM, \"UiMode\"},
    {Uniform::Index::UI_COLOR, Uniform::Type::UNIFORM, \"UiColor\"},
};"""
if uniforms_old not in text:
    raise SystemExit('ProgramUniforms anchor not found')
text = text.replace(uniforms_old, uniforms_new, 1)

text = text.replace('  out vec4 cubeWorldPosition;', '  out highp vec4 cubeWorldPosition;', 1)
text = text.replace('  in lowp vec4 cubeWorldPosition;', '  in highp vec4 cubeWorldPosition;', 1)

shader_anchor = '  uniform highp mat4 DepthProjectionMatrix[NUM_VIEWS];\n'
shader_uniforms = """  uniform highp mat4 DepthProjectionMatrix[NUM_VIEWS];
  uniform highp vec3 LightDirection;
  uniform highp vec3 LightTint;
  uniform highp float AmbientStrength;
  uniform highp float KeyIntensity;
  uniform highp float Exposure;
  uniform highp float UiMode;
  uniform highp vec3 UiColor;
"""
if shader_anchor not in text:
    raise SystemExit('Fragment shader uniform anchor not found')
text = text.replace(shader_anchor, shader_uniforms, 1)

old_output = 'outColor = vec4(fragmentColor.rgb, fragmentColor.a * visibility);'
lit_output = """// Flat geometric normal reconstructed from world-space derivatives. Imported
// glTF models will later use authored vertex normals.
highp vec3 dpdx = dFdx(cubeWorldPosition.xyz);
highp vec3 dpdy = dFdy(cubeWorldPosition.xyz);
highp vec3 surfaceNormal = normalize(cross(dpdx, dpdy));
if (!gl_FrontFacing) {
    surfaceNormal = -surfaceNormal;
}
highp float nDotL = max(dot(surfaceNormal, normalize(LightDirection)), 0.0f);
highp vec3 litColor = fragmentColor.rgb *
    (vec3(AmbientStrength) + LightTint * (KeyIntensity * nDotL));
litColor *= exp2(Exposure);
highp vec3 finalColor = mix(litColor, UiColor, clamp(UiMode, 0.0f, 1.0f));
outColor = vec4(finalColor, fragmentColor.a * visibility);"""
if old_output not in text:
    raise SystemExit('Filtered-depth output anchor not found')
text = text.replace(old_output, lit_output, 1)

render_loop = re.compile(
    r"    for \(const auto& trackedController : scene\.TrackedControllers\) \{.*?    GL\(glBindVertexArray\(0\)\);",
    re.S,
)

replacement = r"""    // Quest3 MR Model Viewer v0.2.0 lighting lab.
    // Top-to-bottom: Ambient, Key, Azimuth, Elevation, Warmth, Exposure.
    static float lightSliders[6] = {0.26f, 0.45f, 0.58f, 0.55f, 0.50f, 0.50f};
    static const float defaultLightSliders[6] = {0.26f, 0.45f, 0.58f, 0.55f, 0.50f, 0.50f};

    constexpr float kPanelZ = -0.18f;
    constexpr float kSliderHalfWidth = 0.080f;
    constexpr float kSliderTopY = 0.100f;
    constexpr float kSliderStep = 0.035f;

    Matrix4f anchorPose;
    Matrix4f pointerTipMatrix;
    const bool haveLightingPalette = scene.TrackedControllers.size() >= 2;
    if (haveLightingPalette) {
        anchorPose = Matrix4f(scene.TrackedControllers[0].Pose);
        const Matrix4f pointerPose(scene.TrackedControllers[1].Pose);
        pointerTipMatrix = pointerPose * Matrix4f::Translation(0.0f, 0.0f, -0.080f);

        const float dx = pointerTipMatrix.M[0][3] - anchorPose.M[0][3];
        const float dy = pointerTipMatrix.M[1][3] - anchorPose.M[1][3];
        const float dz = pointerTipMatrix.M[2][3] - anchorPose.M[2][3];
        const float localX =
  anchorPose.M[0][0] * dx + anchorPose.M[1][0] * dy + anchorPose.M[2][0] * dz;
        const float localY =
  anchorPose.M[0][1] * dx + anchorPose.M[1][1] * dy + anchorPose.M[2][1] * dz;
        const float localZ =
  anchorPose.M[0][2] * dx + anchorPose.M[1][2] * dy + anchorPose.M[2][2] * dz;

        if (std::abs(localZ - kPanelZ) < 0.055f) {
  for (int i = 0; i < 6; ++i) {
      const float rowY = kSliderTopY - float(i) * kSliderStep;
      if (std::abs(localY - rowY) < 0.016f &&
          localX >= -kSliderHalfWidth - 0.012f &&
          localX <= kSliderHalfWidth + 0.012f) {
          lightSliders[i] = std::max(
              0.0f,
              std::min(
                  1.0f,
                  (localX + kSliderHalfWidth) / (2.0f * kSliderHalfWidth)));
      }
  }
  const float resetY = kSliderTopY - 6.0f * kSliderStep - 0.012f;
  if (std::abs(localX) < 0.025f && std::abs(localY - resetY) < 0.018f) {
      for (int i = 0; i < 6; ++i) {
          lightSliders[i] = defaultLightSliders[i];
      }
  }
        }
    }

    const float ambientStrength = 0.02f + lightSliders[0] * 0.78f;
    const float keyIntensity = lightSliders[1] * 2.0f;
    const float azimuth = (lightSliders[2] * 2.0f - 1.0f) * 3.14159265f;
    const float elevation = -0.34906585f + lightSliders[3] * 1.74532925f;
    const float warmth = lightSliders[4] * 2.0f - 1.0f;
    const float exposureStops = -2.0f + lightSliders[5] * 4.0f;

    const float cosElevation = std::cos(elevation);
    const float lightDirection[3] = {
        cosElevation * std::cos(azimuth),
        std::sin(elevation),
        cosElevation * std::sin(azimuth)};

    float lightTint[3] = {1.0f, 1.0f, 1.0f};
    if (warmth >= 0.0f) {
        lightTint[1] = 1.0f - 0.16f * warmth;
        lightTint[2] = 1.0f - 0.32f * warmth;
    } else {
        const float cool = -warmth;
        lightTint[0] = 1.0f - 0.20f * cool;
        lightTint[1] = 1.0f - 0.08f * cool;
    }

    GL(glUniform3fv(
        scene.BoxDepthSpaceOcclusionProgram.GetUniformLocationOrDie(Uniform::Index::LIGHT_DIRECTION),
        1,
        lightDirection));
    GL(glUniform3fv(
        scene.BoxDepthSpaceOcclusionProgram.GetUniformLocationOrDie(Uniform::Index::LIGHT_TINT),
        1,
        lightTint));
    GL(glUniform1f(
        scene.BoxDepthSpaceOcclusionProgram.GetUniformLocationOrDie(Uniform::Index::AMBIENT_STRENGTH),
        ambientStrength));
    GL(glUniform1f(
        scene.BoxDepthSpaceOcclusionProgram.GetUniformLocationOrDie(Uniform::Index::KEY_INTENSITY),
        keyIntensity));
    GL(glUniform1f(
        scene.BoxDepthSpaceOcclusionProgram.GetUniformLocationOrDie(Uniform::Index::EXPOSURE),
        exposureStops));
    GL(glUniform1f(
        scene.BoxDepthSpaceOcclusionProgram.GetUniformLocationOrDie(Uniform::Index::UI_MODE),
        0.0f));
    GL(glUniform3f(
        scene.BoxDepthSpaceOcclusionProgram.GetUniformLocationOrDie(Uniform::Index::UI_COLOR),
        1.0f,
        1.0f,
        1.0f));

    for (const auto& trackedController : scene.TrackedControllers) {
        const Matrix4f pose(trackedController.Pose);
        const Matrix4f offset = Matrix4f::Translation(0, 0, -0.25);
        const Matrix4f scale = Matrix4f::Scaling(0.1, 0.1, 0.1);
        const Matrix4f model = pose * offset * scale;
        GL(glUniformMatrix4fv(
  scene.BoxDepthSpaceOcclusionProgram.GetUniformLocationOrDie(
      Uniform::Index::MODEL_MATRIX),
  1,
  GL_TRUE,
  &model.M[0][0]));
        GL(glDrawElements(GL_TRIANGLES, scene.Box.GetIndexCount(), GL_UNSIGNED_SHORT, NULL));
    }

    if (haveLightingPalette) {
        const auto drawUiCube = [&](const Matrix4f& model, float r, float g, float b) {
  GL(glUniform1f(
      scene.BoxDepthSpaceOcclusionProgram.GetUniformLocationOrDie(Uniform::Index::UI_MODE),
      1.0f));
  GL(glUniform3f(
      scene.BoxDepthSpaceOcclusionProgram.GetUniformLocationOrDie(Uniform::Index::UI_COLOR),
      r,
      g,
      b));
  GL(glUniformMatrix4fv(
      scene.BoxDepthSpaceOcclusionProgram.GetUniformLocationOrDie(
          Uniform::Index::MODEL_MATRIX),
      1,
      GL_TRUE,
      &model.M[0][0]));
  GL(glDrawElements(GL_TRIANGLES, scene.Box.GetIndexCount(), GL_UNSIGNED_SHORT, NULL));
        };

        for (int i = 0; i < 6; ++i) {
  const float rowY = kSliderTopY - float(i) * kSliderStep;
  const float fullWidth = 2.0f * kSliderHalfWidth;
  const float fillWidth = std::max(0.004f, fullWidth * lightSliders[i]);
  const float fillCenterX = -kSliderHalfWidth + fillWidth * 0.5f;
  const float knobX = -kSliderHalfWidth + fullWidth * lightSliders[i];

  const Matrix4f track = anchorPose *
      Matrix4f::Translation(0.0f, rowY, kPanelZ) *
      Matrix4f::Scaling(kSliderHalfWidth, 0.0045f, 0.0025f);
  drawUiCube(track, 0.055f, 0.065f, 0.080f);

  const Matrix4f fill = anchorPose *
      Matrix4f::Translation(fillCenterX, rowY, kPanelZ - 0.003f) *
      Matrix4f::Scaling(fillWidth * 0.5f, 0.0065f, 0.0035f);
  drawUiCube(fill, 0.12f, 0.62f, 0.92f);

  const Matrix4f knob = anchorPose *
      Matrix4f::Translation(knobX, rowY, kPanelZ - 0.007f) *
      Matrix4f::Scaling(0.0075f, 0.0110f, 0.0050f);
  drawUiCube(knob, 0.94f, 0.96f, 1.00f);

  const Matrix4f marker = anchorPose *
      Matrix4f::Translation(-kSliderHalfWidth - 0.019f, rowY, kPanelZ) *
      Matrix4f::Scaling(0.0022f + float(i) * 0.0011f, 0.0050f, 0.0030f);
  drawUiCube(marker, 0.70f, 0.74f, 0.82f);
        }

        const float resetY = kSliderTopY - 6.0f * kSliderStep - 0.012f;
        const Matrix4f resetPad = anchorPose *
  Matrix4f::Translation(0.0f, resetY, kPanelZ) *
  Matrix4f::Scaling(0.022f, 0.012f, 0.004f);
        drawUiCube(resetPad, 0.95f, 0.55f, 0.12f);

        const Matrix4f pointerMarker =
  pointerTipMatrix * Matrix4f::Scaling(0.007f, 0.007f, 0.007f);
        drawUiCube(pointerMarker, 1.0f, 1.0f, 1.0f);

        GL(glUniform1f(
  scene.BoxDepthSpaceOcclusionProgram.GetUniformLocationOrDie(Uniform::Index::UI_MODE),
  0.0f));
    }

    GL(glBindVertexArray(0));"""

text, count = render_loop.subn(replacement, text, count=1)
if count != 1:
    raise SystemExit(f'Expected one controller render loop, patched {count}')

source_path.write_text(text)
print('Directional model lighting: ON')
print('Physical two-controller lighting palette: ON')
print('Sliders: Ambient / Key / Azimuth / Elevation / Warmth / Exposure')
print('Reset pad: ON')
