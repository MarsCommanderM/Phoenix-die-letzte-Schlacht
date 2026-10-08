#pragma once

#include <AzCore/std/string/string_view.h>

namespace Phoenix
{
    //! Build-time and runtime feature gates.
    //!
    //! Release builds must contain no unintended experimental flag; see
    //! docs/tdd/10-risks.md. The set is closed on purpose: a flag that is not
    //! listed here cannot be queried, so flags cannot accumulate unnoticed in
    //! scattered #ifdefs.
    enum class FeatureFlag
    {
        ExperimentalRendering,
        ExperimentalAI,
        ExperimentalTraversal,
        MultiplayerPrototype,
        DebugVisualization,
        PostLaunchFeature
    };

    //! Stable name, used in configuration and diagnostics.
    AZStd::string_view ToString(FeatureFlag flag);

    //! True when the flag is enabled for this build and configuration.
    bool IsFeatureEnabled(FeatureFlag flag);

    //! True when any experimental flag is enabled. Release packaging asserts
    //! this is false rather than trusting that nobody left one on.
    bool AnyExperimentalFeatureEnabled();
} // namespace Phoenix
