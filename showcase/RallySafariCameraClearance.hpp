#pragma once

#include <concepts>

#include "threepp/geometries/BoxGeometry.hpp"
#include "threepp/extras/core/NoiseUtils.hpp"
#include "threepp/math/Matrix4.hpp"
#include "threepp/objects/Group.hpp"
#include "threepp/objects/Mesh.hpp"

#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <memory>
#include <limits>
#include <optional>
#include <stdexcept>
#include <string>
#include <vector>

namespace rally {

inline constexpr std::size_t safariCameraBarrierLimit = 24;
inline constexpr float safariCameraSeparation = .02f;
inline constexpr float safariCameraLookahead = .55f;
inline constexpr float safariCameraMaxPredictionSpeed = 60.f;
inline constexpr float safariCameraMaxPredictionVerticalSpeed = 20.f;

struct SafariCameraClearanceReport {
    std::size_t testedBoxes = 0;
    bool shortened = false;
    bool targetInsideBarrier = false;
    bool invalidInput = false;
    bool barrierLimitExceeded = false;
    bool scaledBarrier = false;
    float boomFraction = 1;
    float forecastBoomFraction = 1;
    bool hardClamped = false;
    bool forecastRejected = false;
    bool forecastTargetInsideBarrier = false;
};

struct SafariCameraTracking {
    threepp::Vector3 unobstructedPosition;
    threepp::Vector3 previousTarget;
    float boomFraction = 1;
    bool initialized = false;
};

namespace safari_camera_detail {
inline bool finite(const threepp::Vector3& v) {
    return std::isfinite(v.x) && std::isfinite(v.y) && std::isfinite(v.z);
}

// A finite segment, parameterized by t in [0,1]. An unbounded ray query
// would also accept a gate beyond the desired camera.
inline std::optional<double> segmentEntry(const threepp::Vector3& start,
                                          const threepp::Vector3& end,
                                          const threepp::Box3& box) {
    double entry = 0, exit = 1;
    for (std::size_t axis = 0; axis < 3; ++axis) {
        const double origin = start[axis];
        const double direction = static_cast<double>(end[axis]) - origin;
        if (direction == 0) {
            if (origin < box.min()[axis] || origin > box.max()[axis]) return {};
            continue;
        }
        double near = (box.min()[axis] - origin) / direction;
        double far = (box.max()[axis] - origin) / direction;
        if (near > far) std::swap(near, far);
        entry = std::max(entry, near);
        exit = std::min(exit, far);
        if (entry > exit) return {};
    }
    return entry;
}
struct PreparedBarrier {
    threepp::Matrix4 inverse;
    threepp::Box3 padded;
    threepp::Vector3 target, camera;
};

struct PreparedBarriers {
    std::array<PreparedBarrier, safariCameraBarrierLimit> boxes;
    std::size_t count = 0;
};

inline PreparedBarriers prepare(const threepp::Vector3& target,
                                const threepp::Vector3& camera,
                                const std::vector<std::shared_ptr<threepp::Mesh>>& barriers,
                                float clearance,
                                SafariCameraClearanceReport& result) {
    using namespace threepp;
    PreparedBarriers prepared;
    result.barrierLimitExceeded = barriers.size() > safariCameraBarrierLimit;
    if (result.barrierLimitExceeded || !finite(target) || !finite(camera)
        || !std::isfinite(clearance) || clearance < 0) {
        result.invalidInput = true;
        return prepared;
    }
    for (const auto& mesh : barriers) {
        // Keep the cold query bounded to simple boxes too: the actual gates
        // have 24 vertices each, so computing their first bounds is cheap.
        const auto geometry = mesh ? mesh->geometry() : nullptr;
        const auto* boxGeometry = dynamic_cast<const BoxGeometry*>(geometry.get());
        if (!boxGeometry || boxGeometry->parameters.widthSegments != 1
            || boxGeometry->parameters.heightSegments != 1 || boxGeometry->parameters.depthSegments != 1) {
            result.invalidInput = true;
            continue;
        }
        mesh->updateWorldMatrix(true, false);
        const auto& world = *mesh->matrixWorld;
        const auto& w = world.elements;
        if (!std::all_of(w.begin(), w.end(), [](float v) { return std::isfinite(v); })
            || w[3] != 0 || w[7] != 0 || w[11] != 0 || w[15] != 1
            || !std::isfinite(world.determinant()) || world.determinant() == 0) {
            result.invalidInput = true;
            continue;
        }
        Matrix4 inverse = world;
        inverse.invert();
        const auto& e = inverse.elements;
        if (!std::all_of(e.begin(), e.end(), [](float v) { return std::isfinite(v); })) {
            result.invalidInput = true;
            continue;
        }
        // Each inverse linear row maps a world-space sphere to a local-axis
        // extent. For orthogonal scales this is clearance / abs(axis scale).
        // Row norms remain conservative with reflected or sheared parents;
        // using world clearance directly in scaled local units would not.
        const Vector3 padding(clearance * std::hypot(e[0], e[4], e[8]),
                              clearance * std::hypot(e[1], e[5], e[9]),
                              clearance * std::hypot(e[2], e[6], e[10]));
        if (!finite(padding)) {
            result.invalidInput = true;
            continue;
        }
        for (int column : {0, 4, 8}) {
            const float axisLength = std::hypot(w[column], w[column + 1], w[column + 2]);
            result.scaledBarrier |= std::abs(axisLength - 1) > 1e-5f;
        }
        if (!geometry->boundingBox) geometry->computeBoundingBox();
        Box3 padded = *geometry->boundingBox;
        padded.expandByVector(padding);
        const auto localTarget = target.clone().applyMatrix4(inverse);
        const auto localDesired = camera.clone().applyMatrix4(inverse);
        if (padded.isEmpty() || !finite(padded.min()) || !finite(padded.max())
            || !finite(localTarget) || !finite(localDesired)) {
            result.invalidInput = true;
            continue;
        }
        ++result.testedBoxes;
        result.targetInsideBarrier |= padded.containsPoint(localTarget);
        prepared.boxes[prepared.count++] = {inverse, padded, localTarget, localDesired};
    }
    return prepared;
}

inline double boomLength(const threepp::Vector3& target, const threepp::Vector3& camera) {
    return std::hypot(static_cast<double>(camera.x) - target.x,
                      static_cast<double>(camera.y) - target.y,
                      static_cast<double>(camera.z) - target.z);
}

inline float hardFraction(const PreparedBarriers& prepared, double length,
                          SafariCameraClearanceReport& report) {
    if (report.invalidInput || report.targetInsideBarrier || length < 1e-6) return 1;
    double firstEntry = 1;
    bool blocked = false;
    for (std::size_t i = 0; i < prepared.count; ++i) {
        const auto& box = prepared.boxes[i];
        if (const auto entry = segmentEntry(box.target, box.camera, box.padded)) {
            firstEntry = std::min(firstEntry, *entry);
            blocked = true;
        }
    }
    if (!blocked) return 1;
    // Stop a small world distance before the expanded surface to avoid an
    // on-boundary camera. No finite safe boom exists if that reaches target.
    const double fraction = firstEntry - safariCameraSeparation / length;
    if (fraction <= 0) {
        report.invalidInput = true;
        return 1;
    }
    return static_cast<float>(fraction);
}

inline threepp::Vector3 positionAtFraction(const threepp::Vector3& target,
                                          const threepp::Vector3& camera,
                                          float fraction) {
    if (fraction == 1) return camera;
    return {static_cast<float>(target.x + (static_cast<double>(camera.x) - target.x) * fraction),
            static_cast<float>(target.y + (static_cast<double>(camera.y) - target.y) * fraction),
            static_cast<float>(target.z + (static_cast<double>(camera.z) - target.z) * fraction)};
}

struct ParamPoint { double t, s; };

// Clip the (boom fraction t, future time s) unit square by the six local
// box halfplanes. This detects a thin beam even when it is crossed and left
// between the present and the horizon. A convex polygon gains at most one
// vertex per halfplane, so 16 slots exceed the maximum of 4 + 6 vertices.
inline std::optional<double> sweptEntry(const PreparedBarrier& box,
                                        const threepp::Vector3& velocity) {
    std::array<ParamPoint, 16> polygon{}, output{};
    polygon[0] = {0, 0}; polygon[1] = {1, 0};
    polygon[2] = {1, 1}; polygon[3] = {0, 1};
    std::size_t count = 4;
    const auto& e = box.inverse.elements;
    for (std::size_t axis = 0; axis < 3; ++axis) {
        const double origin = box.target[axis];
        const double alongBoom = static_cast<double>(box.camera[axis]) - origin;
        const double alongTime = safariCameraLookahead *
            (static_cast<double>(e[axis]) * velocity.x + static_cast<double>(e[axis + 4]) * velocity.y
             + static_cast<double>(e[axis + 8]) * velocity.z);
        for (int side : {-1, 1}) {
            const double a = side * alongBoom, b = side * alongTime;
            const double c = side < 0 ? box.padded.min()[axis] - origin : origin - box.padded.max()[axis];
            auto value = [&](const ParamPoint& p) { return a * p.t + b * p.s + c; };
            std::size_t outputCount = 0;
            auto previous = polygon[count - 1];
            double previousValue = value(previous);
            for (std::size_t i = 0; i < count; ++i) {
                const auto current = polygon[i];
                const double currentValue = value(current);
                if ((previousValue <= 0) != (currentValue <= 0)) {
                    const double u = previousValue / (previousValue - currentValue);
                    output[outputCount++] = {previous.t + (current.t - previous.t) * u,
                                             previous.s + (current.s - previous.s) * u};
                }
                if (currentValue <= 0) output[outputCount++] = current;
                previous = current;
                previousValue = currentValue;
            }
            if (outputCount == 0) return {};
            count = outputCount;
            polygon.swap(output);
        }
    }
    double first = 1;
    for (std::size_t i = 0; i < count; ++i) first = std::min(first, polygon[i].t);
    return std::clamp(first, 0., 1.);
}

inline float forecastFraction(const PreparedBarriers& prepared, double length,
                              const threepp::Vector3& velocity, SafariCameraClearanceReport& report) {
    if (length < 1e-6) return 1;
    double firstEntry = 1;
    bool blocked = false;
    for (std::size_t i = 0; i < prepared.count; ++i) {
        if (const auto entry = sweptEntry(prepared.boxes[i], velocity)) {
            // If the future target itself enters a box, shortening toward
            // t=0 cannot solve it. Do not anticipate by easing onto the car.
            // Keep current-frame safety active and report this forecast gap.
            if (*entry <= 1e-8) {
                report.forecastTargetInsideBarrier = true;
                continue;
            }
            firstEntry = std::min(firstEntry, *entry);
            blocked = true;
        }
    }
    return blocked ? static_cast<float>(std::max(0., firstEntry - safariCameraSeparation / length)) : 1;
}
} // namespace safari_camera_detail

// Stateless exact current-frame safety clamp. Call only for Safari exterior
// views, after an existing lerp and before lookAt, with its unchanged target.
// A target inside a padded box or invalid input preserves the supplied camera
// and reports the failure instead of collapsing the camera onto the car.
[[nodiscard]] inline threepp::Vector3 safariClearCamera(
        const threepp::Vector3& target,
        const threepp::Vector3& desired,
        const std::vector<std::shared_ptr<threepp::Mesh>>& barriers,
        float clearance = .30f,
        SafariCameraClearanceReport* report = nullptr) {
    SafariCameraClearanceReport result;
    const auto prepared = safari_camera_detail::prepare(target, desired, barriers, clearance, result);
    result.boomFraction = safari_camera_detail::hardFraction(prepared, safari_camera_detail::boomLength(target, desired), result);
    result.shortened = result.boomFraction < 1;
    result.hardClamped = result.shortened;
    if (report) *report = result;
    return safari_camera_detail::positionAtFraction(target, desired, result.boomFraction);
}

// Replace Safari's exterior camera lerp with this helper; desired is the RAW
// unobstructed camera, never last frame's shortened position. The independent
// base retains the original 5/s lerp. A continuous .55 s translational forecast
// eases the boom fraction at 5/s contraction and 2/s release. Exact present
// safety takes priority if motion changes faster than that forecast predicts.
// worldVelocity supplies actual horizontal drift; target Y velocity is measured
// from previousTarget so rising ground is included even with motion.y == 0.
// Predictions above 60 m/s total, 20 m/s vertical, or a .1 s update interval
// are rejected explicitly; current-frame safety still applies.
//
// Supply the 8 gate beams and 16 posts only. Each query prepares at most 24
// simple local boxes once, updating mesh/ancestors without descending through
// the scene. Geometry bounds are cached on first use; no vertices, body poses,
// materials, visibility or colliders are changed. cut resets both base/fraction.
[[nodiscard]] inline threepp::Vector3 safariTrackClearCamera(
        const threepp::Vector3& target,
        const threepp::Vector3& desired,
        const threepp::Vector3& worldVelocity,
        float dt,
        bool cut,
        const std::vector<std::shared_ptr<threepp::Mesh>>& barriers,
        SafariCameraTracking& state,
        SafariCameraClearanceReport* report = nullptr,
        float clearance = .30f) {
    SafariCameraClearanceReport result;
    if (!safari_camera_detail::finite(target) || !safari_camera_detail::finite(desired)
        || !std::isfinite(dt) || dt < 0) {
        result.invalidInput = true;
        if (report) *report = result;
        return desired;
    }
    const bool reset = cut || !state.initialized;
    auto predictedVelocity = worldVelocity;
    predictedVelocity.y = reset || dt < 1e-6f ? 0 : (target.y - state.previousTarget.y) / dt;
    state.previousTarget = target;
    result.forecastRejected = !safari_camera_detail::finite(predictedVelocity)
        || std::abs(predictedVelocity.y) > safariCameraMaxPredictionVerticalSpeed
        || std::hypot(predictedVelocity.x, predictedVelocity.y, predictedVelocity.z) > safariCameraMaxPredictionSpeed
        || dt > .1f;
    if (reset) {
        state.unobstructedPosition = desired;
        state.boomFraction = 1;
        state.initialized = true;
    } else {
        state.unobstructedPosition.lerp(desired, 1 - std::exp(-5 * dt));
    }
    const auto prepared = safari_camera_detail::prepare(target, state.unobstructedPosition, barriers, clearance, result);
    const double length = safari_camera_detail::boomLength(target, state.unobstructedPosition);
    const float safeFraction = safari_camera_detail::hardFraction(prepared, length, result);
    if (result.invalidInput || result.targetInsideBarrier) {
        state.boomFraction = 1;
    } else {
        if (!result.forecastRejected)
            result.forecastBoomFraction = safari_camera_detail::forecastFraction(prepared, length, predictedVelocity, result);
        const float rate = result.forecastBoomFraction < state.boomFraction ? 5.f : 2.f;
        const float eased = state.boomFraction + (result.forecastBoomFraction - state.boomFraction) * (1 - std::exp(-rate * dt));
        state.boomFraction = std::min(eased, safeFraction);
        result.hardClamped = safeFraction < eased;
        if (safeFraction == 1 && result.forecastBoomFraction == 1 && state.boomFraction > 1 - 1e-5f)
            state.boomFraction = 1;
    }
    result.boomFraction = state.boomFraction;
    result.shortened = state.boomFraction < 1;
    if (report) *report = result;
    return safari_camera_detail::positionAtFraction(target, state.unobstructedPosition, state.boomFraction);
}

struct SafariCameraTrackingRegressionReport {
    float flatMaxFractionStep = 0, flatMinBoomFraction = 1;
    int flatFirstBaselineCollisionFrame = -1, flatFirstAnticipationFrame = -1;
    int flatAnticipatingFramesBeforeCollision = 0, flatAnticipatingFramesBeforeTargetZero = 0;
    int flatBaselineObstructedFrames = 0, flatHardClampFrames = 0, flatSafetySamples = 0;
    float nativeMaxFractionStep = 0, nativeMaxSnapIntervalStep = 0, nativeMinBoomFraction = 1;
    int nativeAnticipatingFramesBeforeSnap = 0, nativeHardClampFrames = 0;

    [[nodiscard]] std::string summary() const {
        return "flat maxStep=" + std::to_string(flatMaxFractionStep)
            + " minBoom=" + std::to_string(flatMinBoomFraction)
            + " firstBaselineCollision=" + std::to_string(flatFirstBaselineCollisionFrame)
            + " firstAnticipation=" + std::to_string(flatFirstAnticipationFrame)
            + " anticipationBeforeCollision=" + std::to_string(flatAnticipatingFramesBeforeCollision)
            + " legacyAnticipationBeforeTargetZero=" + std::to_string(flatAnticipatingFramesBeforeTargetZero)
            + " baselineObstructedFrames=" + std::to_string(flatBaselineObstructedFrames)
            + " hardClampFrames=" + std::to_string(flatHardClampFrames)
            + " safetySamples=" + std::to_string(flatSafetySamples)
            + "; native maxStep=" + std::to_string(nativeMaxFractionStep)
            + " snapIntervalMaxStep=" + std::to_string(nativeMaxSnapIntervalStep)
            + " minBoom=" + std::to_string(nativeMinBoomFraction)
            + " anticipationBeforeSnap=" + std::to_string(nativeAnticipatingFramesBeforeSnap)
            + " hardClampFrames=" + std::to_string(nativeHardClampFrames);
    }
};

inline SafariCameraTrackingRegressionReport safariCameraTrackingRegressions() {
    using namespace threepp;
    auto check = [](bool ok, const std::string& message) {
        if (!ok) throw std::runtime_error(message);
    };
    SafariCameraTrackingRegressionReport statistics;
    constexpr float dt = 1.f / 30;
    SafariCameraTracking clearState;
    SafariCameraClearanceReport report;
    Vector3 expected;
    for (int frame = 0; frame < 120; ++frame) {
        const Vector3 desired(frame * .2f, 3, frame * .13f);
        if (frame == 0) expected = desired;
        else expected.lerp(desired, 1 - std::exp(-5 * dt));
        const auto camera = safariTrackClearCamera(Vector3(0, 1.1f, 0), desired, Vector3(6, 0, 3.9f),
                                                   dt, frame == 0, {}, clearState, &report);
        check(camera.equals(expected) && clearState.unobstructedPosition.equals(expected)
                  && report.boomFraction == 1 && report.testedBoxes == 0,
              "Unobstructed tracking changes the original 5/s lerp");
    }

    auto beam = Mesh::create(BoxGeometry::create(9, .42f, .2f)); beam->position.y = 3.7f;
    std::vector<std::shared_ptr<Mesh>> barriers{beam};
    const Box3 paddedBeam(Vector3(-4.8f, 3.19f, -.4f), Vector3(4.8f, 4.21f, .4f));
    SafariCameraTracking moving;
    float previousFraction = 1, maxFractionStep = 0;
    Vector3 expectedBase;
    for (int frame = 0; frame < 240; ++frame) {
        const float z = -18 + 13.5f * frame * dt;
        const Vector3 target(0, 1.1f, z), desired(0, 3.9f, z - 6.6f);
        if (frame == 0) expectedBase = desired;
        else expectedBase.lerp(desired, 1 - std::exp(-5 * dt));
        const auto camera = safariTrackClearCamera(target, desired, Vector3(0, 0, 13.5f),
                                                   dt, frame == 0, barriers, moving, &report);
        maxFractionStep = std::max(maxFractionStep, std::abs(report.boomFraction - previousFraction));
        previousFraction = report.boomFraction;
        statistics.flatMaxFractionStep = maxFractionStep;
        statistics.flatMinBoomFraction = std::min(statistics.flatMinBoomFraction, report.boomFraction);
        check(!report.invalidInput && !report.targetInsideBarrier && report.testedBoxes == 1
                  && moving.unobstructedPosition.equals(expectedBase),
              "Moving forecast compounds its shortened camera or loses its bounded query");
        const bool baselineObstructed = safari_camera_detail::segmentEntry(target, expectedBase, paddedBeam).has_value();
        if (baselineObstructed) {
            ++statistics.flatBaselineObstructedFrames;
            if (statistics.flatFirstBaselineCollisionFrame < 0) statistics.flatFirstBaselineCollisionFrame = frame;
        }
        if (report.shortened) {
            if (statistics.flatFirstAnticipationFrame < 0) statistics.flatFirstAnticipationFrame = frame;
            if (statistics.flatFirstBaselineCollisionFrame < 0) ++statistics.flatAnticipatingFramesBeforeCollision;
            if (z < 0) ++statistics.flatAnticipatingFramesBeforeTargetZero;
        }
        if (report.hardClamped) ++statistics.flatHardClampFrames;
        // Independent world-space samples along this known straight boom.
        // The actual beam plus .30m padding must exclude its entire segment.
        for (int sample = 0; sample <= 128; ++sample) {
            ++statistics.flatSafetySamples;
            check(!paddedBeam.containsPoint(target.clone().lerp(camera, sample / 128.f)),
                  "Anticipating camera boom enters the padded beam at frame=" + std::to_string(frame)
                      + " sample=" + std::to_string(sample) + "; " + statistics.summary());
        }
    }
    // Anticipation is measured before the FULL base boom would first touch
    // the beam, which occurs after the target/car has passed it. An emergency
    // hard clamp need not fire when anticipation already keeps that boom safe.
    check(maxFractionStep < .04f && statistics.flatAnticipatingFramesBeforeCollision >= 8
              && statistics.flatBaselineObstructedFrames > 0,
          "13.5m/s narrow-beam passage snaps or does not anticipate before baseline collision; " + statistics.summary());
    check(moving.boomFraction > .99f, "Moving boom fails to release after crossing");

    const Vector3 fixedTarget(0, 1.1f, -3), fixedDesired(0, 5, 3);
    SafariCameraTracking fixed;
    const auto fixedSafe = safariTrackClearCamera(fixedTarget, fixedDesired, Vector3(), dt, true, barriers, fixed);
    for (int frame = 0; frame < 120; ++frame) {
        const auto camera = safariTrackClearCamera(fixedTarget, fixedDesired, Vector3(), dt, false, barriers, fixed);
        check(fixed.unobstructedPosition.equals(fixedDesired) && camera.distanceTo(fixedSafe) < 1e-5f
                  && fixed.boomFraction > .5f, "Stationary clamp compounds into the target");
    }
    beam->position.z = 100;
    for (int frame = 0; frame < 180; ++frame) {
        const float before = fixed.boomFraction;
        const auto camera = safariTrackClearCamera(fixedTarget, fixedDesired, Vector3(), dt, false, barriers, fixed, &report);
        check(fixed.boomFraction >= before && fixed.boomFraction - before < .04f && !report.hardClamped
                  && camera.distanceTo(fixedDesired) <= fixedSafe.distanceTo(fixedDesired),
              "Boom release is not smooth and monotonic");
    }
    check(fixed.boomFraction == 1, "Released fraction fails to return to exact identity");
    fixed.boomFraction = .3f; fixed.previousTarget.y = 100;
    const Vector3 cutDesired(7, 3, -8);
    check(safariTrackClearCamera(fixedTarget, cutDesired, Vector3(), dt, true, barriers, fixed, &report).equals(cutDesired)
              && fixed.boomFraction == 1 && fixed.unobstructedPosition.equals(cutDesired)
              && fixed.previousTarget.equals(fixedTarget) && !report.forecastRejected,
          "Camera cut retains old contraction/base/vertical velocity");

    beam->position.z = 0;
    const auto hardSafe = safariClearCamera(fixedTarget, fixedDesired, barriers);
    for (float excessive : {1e20f, std::numeric_limits<float>::infinity()}) {
        const auto camera = safariTrackClearCamera(fixedTarget, fixedDesired, Vector3(excessive, 0, 0),
                                                   dt, true, barriers, fixed, &report);
        check(report.forecastRejected && report.hardClamped && camera.distanceTo(hardSafe) < 1e-5f,
              "Extreme/non-finite prediction bypasses immediate safety");
    }
    auto post = Mesh::create(BoxGeometry::create(.16f, 3.7f, .16f)); post->position.y = 1.85f;
    const Vector3 behind(0, 3, -6);
    check(safariTrackClearCamera(fixedTarget, behind, Vector3(0, 0, 13.5f), dt, true, {post}, fixed, &report).equals(behind)
              && report.forecastTargetInsideBarrier && !report.targetInsideBarrier && report.boomFraction == 1,
          "Future target entering a post eases the camera onto the car");

    // Frozen native ride x/z/heading samples from session
    // 20261103-052651-070, internal frames135..205 (capture45..115).
    // The actual RallyDetail.hpp terrain formula reconstructs target/raw
    // camera Y, including the climb at the former captured79->80 snap.
    constexpr float native[][3] = {
        {45.868187f,72.7926712f,2.49665713f},
        {46.1540031f,72.445755f,2.50939322f}, {46.4353676f,72.0953674f,2.52213717f},
        {46.7122688f,71.7414932f,2.5348866f}, {46.9846802f,71.3841324f,2.54762888f},
        {47.2525787f,71.0233078f,2.56035829f}, {47.5159378f,70.6590347f,2.57307005f},
        {47.7747192f,70.2913513f,2.58575058f}, {48.0287628f,69.9205246f,2.59838557f},
        {48.278019f,69.5466309f,2.61096859f}, {48.5224991f,69.1696548f,2.62348747f},
        {48.762207f,68.7896194f,2.63593554f}, {48.9971428f,68.4065475f,2.64830756f},
        {49.2273026f,68.0204849f,2.66059017f}, {49.4526863f,67.6314774f,2.67277575f},
        {49.673214f,67.2397385f,2.68485355f}, {49.8888321f,66.8454361f,2.69680762f},
        {50.0995712f,66.4485855f,2.70862913f}, {50.3054733f,66.049202f,2.72031379f},
        {50.5065765f,65.647316f,2.73185158f}, {50.7029037f,65.242981f,2.74323511f},
        {50.8944931f,64.8362503f,2.75446033f}, {51.081337f,64.4272614f,2.76551628f},
        {51.2633972f,64.0162964f,2.77639055f}, {51.4407387f,63.6033554f,2.78708243f},
        {51.6134224f,63.1884537f,2.79758573f}, {51.781517f,62.7716217f,2.80789542f},
        {51.9450874f,62.3529053f,2.81801152f}, {52.1041946f,61.9323425f,2.82792759f},
        {52.2588921f,61.5100403f,2.83763766f}, {52.4091682f,61.0862846f,2.84713674f},
        {52.5550995f,60.6611099f,2.85642219f}, {52.6967773f,60.23452f,2.86549163f},
        {52.8342857f,59.80653f,2.8743484f}, {52.9677162f,59.3771706f,2.88299179f},
        {53.0971451f,58.9464722f,2.8914187f}, {53.2226677f,58.5144691f,2.89963293f},
        {53.3442955f,58.0814667f,2.9076314f}, {53.4621086f,57.6475258f,2.91541314f},
        {53.57621f,57.2126312f,2.92298412f}, {53.6866913f,56.7767792f,2.93034887f},
        {53.7936516f,56.3399811f,2.93750763f}, {53.8971825f,55.9022484f,2.94446492f},
        {53.9973679f,55.463604f,2.95122671f}, {54.094265f,55.02425f,2.95779228f},
        {54.1879349f,54.5843315f,2.96416378f}, {54.2784767f,54.1438179f,2.97035003f},
        {54.3659821f,53.7026863f,2.97635484f}, {54.4505424f,53.2609215f,2.98218179f},
        {54.5322418f,52.8185234f,2.98783946f}, {54.6111641f,52.3754997f,2.99333358f},
        {54.6873741f,51.9319458f,2.99866557f}, {54.7609177f,51.4881096f,3.0038414f},
        {54.8318863f,51.0439339f,3.00886869f}, {54.9003487f,50.5993729f,3.01375031f},
        {54.9663925f,50.1543999f,3.01849389f}, {55.0300827f,49.7090034f,3.02310777f},
        {55.0914917f,49.2631721f,3.02759528f}, {55.1506767f,48.8169479f,3.03196073f},
        {55.2076759f,48.3705864f,3.03621054f}, {55.2625504f,47.924057f,3.04034853f},
        {55.3153648f,47.4773102f,3.04437685f}, {55.3661804f,47.030304f,3.04830265f},
        {55.4150543f,46.5830078f,3.05213141f}, {55.4620361f,46.1354065f,3.05586481f},
        {55.5071831f,45.6874924f,3.05950785f}, {55.550518f,45.2395172f,3.06306458f},
        {55.5920906f,44.7915001f,3.0665369f}, {55.6319427f,44.3433685f,3.06992555f},
        {55.6701279f,43.8950806f,3.07323694f}, {55.7066803f,43.4466019f,3.07647347f}
    };
    const auto height = [](float x, float z) {
        return 5.5f * std::sin(x * .024f) + 4.f * std::cos(z * .031f)
            + 9.f * (noise::fbm(x * .021f, z * .021f, 256, 71, 4) - .5f) + .17f * std::sin(x * .7f + z * .4f);
    };
    const auto track = [&](float a) {
        const float x = 64 * std::sin(a) + 8 * std::sin(3 * a), z = 90 * std::cos(a);
        return Vector3(x, height(x, z), z);
    };
    constexpr float pi = 3.14159265359f;
    auto gate = Group::create(); gate->position.copy(track(pi / 4));
    const auto ahead = track(pi / 4 + .01f).sub(gate->position);
    gate->rotation.y = std::atan2(ahead.x, ahead.z); gate->add(beam);
    SafariCameraTracking rising;
    previousFraction = 1; maxFractionStep = 0;
    Vector3 previousTarget;
    int sampleIndex = 0, anticipationBeforeSnap = 0;
    float largestSnapIntervalStep = 0;
    for (const auto& row : native) {
        const Vector3 position(row[0], height(row[0], row[1]), row[1]);
        const Vector3 forward(std::sin(row[2]), 0, std::cos(row[2])), right(std::cos(row[2]), 0, -std::sin(row[2]));
        const auto target = position.clone().add(Vector3(0, 1.1f, 0));
        auto desired = position.clone().addScaledVector(forward, -3.7f).addScaledVector(right, 4.1f).add(Vector3(0, 3, 0));
        desired.y = std::max(desired.y, height(desired.x, desired.z) + 1.25f);
        auto velocity = sampleIndex == 0 ? Vector3() : target.clone().sub(previousTarget).multiplyScalar(1 / dt);
        velocity.y = 0; previousTarget = target; // production passes horizontal driver.motion
        const auto camera = safariTrackClearCamera(target, desired, velocity, dt, sampleIndex == 0, barriers, rising, &report);
        const float change = std::abs(report.boomFraction - previousFraction);
        maxFractionStep = std::max(maxFractionStep, change); previousFraction = report.boomFraction;
        if (sampleIndex >= 33 && sampleIndex <= 39) largestSnapIntervalStep = std::max(largestSnapIntervalStep, change);
        if (sampleIndex < 35 && report.shortened) ++anticipationBeforeSnap;
        if (report.hardClamped) ++statistics.nativeHardClampFrames;
        statistics.nativeMaxFractionStep = maxFractionStep;
        statistics.nativeMaxSnapIntervalStep = largestSnapIntervalStep;
        statistics.nativeAnticipatingFramesBeforeSnap = anticipationBeforeSnap;
        statistics.nativeMinBoomFraction = std::min(statistics.nativeMinBoomFraction, report.boomFraction);
        check(!report.invalidInput && !report.targetInsideBarrier && !report.forecastRejected,
              "Native rising-ground forecast rejects valid motion");
        // An independent exact clamp should leave an already safe camera alone.
        check(safariClearCamera(target, camera, barriers).distanceTo(camera) < 2e-4f,
              "Native rising-ground tracking camera violates current clearance");
        ++sampleIndex;
    }
    check(sampleIndex == 71 && anticipationBeforeSnap >= 10 && maxFractionStep < .04f
              && largestSnapIntervalStep < .04f && rising.boomFraction > .95f,
          "Native rising-ground fixture retains the former camera snap or fails to release; " + statistics.summary());
    return statistics;
}

// CPU-only recipe: include this header in rally_vehicle_test.cpp and call
// rally::safariCameraClearanceRegressions() inside its existing try block.
// No renderer/native window, vehicle model or simulation is constructed.
inline SafariCameraTrackingRegressionReport safariCameraClearanceRegressions() {
    using namespace threepp;
    auto check = [](bool ok, const char* message) {
        if (!ok) throw std::runtime_error(message);
    };
    auto beam = Mesh::create(BoxGeometry::create(9, .42f, .2f));
    beam->position.y = 3.7f;
    std::vector<std::shared_ptr<Mesh>> barriers{beam};
    const Vector3 target(0, 3.7f, -3), desired(0, 3.7f, 3);
    SafariCameraClearanceReport report;
    check(safariClearCamera(target, desired, {}).equals(desired), "Empty barriers change camera");
    const auto safe = safariClearCamera(target, desired, barriers, .30f, &report);
    check(report.shortened && report.testedBoxes == 1 && !report.invalidInput
              && std::abs(safe.z + .42f) < 1e-5f && safe.x == 0 && safe.y == desired.y,
          "Direct beam crossing does not stop at radius plus separation");
    check(safariClearCamera(target, safe, barriers).equals(safe), "Resolved boom is not stable");
    check(safariClearCamera(target, Vector3(0, 3.7f, -1), barriers).equals(Vector3(0, 3.7f, -1)),
          "Barrier beyond finite segment falsely clips camera");
    check(safariClearCamera(Vector3(0, 3.7f, -1), target, barriers).equals(target),
          "Barrier behind target falsely clips camera");
    check(safariClearCamera(Vector3(0, 1.1f, -3), Vector3(0, 1.1f, 3), barriers).equals(Vector3(0, 1.1f, 3)),
          "Clear boom below beam changes camera");
    const auto sloped = safariClearCamera(Vector3(0, 1.1f, -3), Vector3(0, 5, 3), barriers);
    check(sloped.y < 3.19f && sloped.y > 3.15f, "Sloped chase boom passes through beam");
    check(std::abs(safariClearCamera(target, desired, barriers, .35f).z + .47f) < 1e-5f,
          "World clearance parameter is ignored");
    const auto inside = Vector3(0, 3.7f, 0);
    check(safariClearCamera(inside, desired, barriers, .30f, &report).equals(desired)
              && report.targetInsideBarrier && !report.shortened,
          "Inside target collapses camera onto car or is not reported");
    check(safariClearCamera(desired, desired, barriers).equals(desired), "Zero boom changes camera");

    auto nearPost = Mesh::create(BoxGeometry::create(.16f, 3.7f, .16f));
    auto farPost = Mesh::create(BoxGeometry::create(.16f, 3.7f, .16f));
    nearPost->position.set(0, 1.85f, -1); farPost->position.set(0, 1.85f, 1);
    const Vector3 postTarget(0, 1.1f, -3), postDesired(0, 1.1f, 3);
    check(std::abs(safariClearCamera(postTarget, postDesired, {farPost, nearPost}).z + 1.40f) < 1e-5f,
          "Nearest gate post depends on barrier order");

    auto gate = Group::create();
    gate->position.set(7, 2, -5); gate->rotation.y = .73f; gate->add(beam);
    beam->updateWorldMatrix(true, false);
    auto worldTarget = Vector3(0, 0, -3).applyMatrix4(*beam->matrixWorld);
    auto worldDesired = Vector3(0, 0, 3).applyMatrix4(*beam->matrixWorld);
    auto worldSafe = safariClearCamera(worldTarget, worldDesired, barriers);
    Matrix4 inverse = *beam->matrixWorld; inverse.invert();
    check(std::abs(worldSafe.clone().applyMatrix4(inverse).z + .42f) < 2e-5f,
          "Yaw-rotated beam crossing loses its local OBB");
    const auto missTarget = Vector3(4.9f, 0, -3).applyMatrix4(*beam->matrixWorld);
    const auto missDesired = Vector3(4.9f, 0, 3).applyMatrix4(*beam->matrixWorld);
    check(safariClearCamera(missTarget, missDesired, barriers).equals(missDesired),
          "Rotated world AABB falsely replaces local OBB");

    gate->scale.set(2, .5f, -3); beam->updateWorldMatrix(true, false);
    worldTarget = Vector3(0, 0, -3).applyMatrix4(*beam->matrixWorld);
    worldDesired = Vector3(0, 0, 3).applyMatrix4(*beam->matrixWorld);
    // Deliberately stale parent and child matrices: helper must update both.
    gate->position.x += 4; worldTarget.x += 4; worldDesired.x += 4;
    worldSafe = safariClearCamera(worldTarget, worldDesired, barriers, .30f, &report);
    inverse.copy(*beam->matrixWorld).invert();
    const auto localSafe = worldSafe.clone().applyMatrix4(inverse);
    check(report.shortened && report.scaledBarrier && !report.invalidInput
              && std::abs((-localSafe.z - .1f) * 3 - .32f) < 3e-5f,
          "Scaled/reflected parent loses world clearance or uses stale matrices");

    gate->position.x += 100;
    auto recovering = worldSafe;
    for (int frame = 0; frame < 120; ++frame) {
        const auto smoothed = recovering.clone().lerp(worldDesired, .08f);
        const auto released = safariClearCamera(worldTarget, smoothed, barriers);
        check(released.equals(smoothed) && released.distanceTo(worldDesired) <= recovering.distanceTo(worldDesired) + 1e-5f,
              "Released boom bypasses or destabilizes caller smoothing");
        recovering = released;
    }
    check(recovering.distanceTo(worldDesired) < .001f, "Released boom fails to recover");
    std::vector<std::shared_ptr<Mesh>> bounded(safariCameraBarrierLimit, beam);
    check(safariClearCamera(worldTarget, worldDesired, bounded, .30f, &report).equals(worldDesired)
              && report.testedBoxes == safariCameraBarrierLimit, "24-box query is not bounded/complete");
    bounded.push_back(beam);
    check(safariClearCamera(worldTarget, worldDesired, bounded, .30f, &report).equals(worldDesired)
              && report.barrierLimitExceeded && report.invalidInput && report.testedBoxes == 0,
          "Over-limit query is silently truncated");
    gate->scale.x = 0;
    check(safariClearCamera(worldTarget, worldDesired, barriers, .30f, &report).equals(worldDesired)
              && report.invalidInput && !report.shortened, "Singular barrier transform is not rejected");
    return safariCameraTrackingRegressions();
}

} // namespace rally
