#include <Phoenix/Core/PhoenixFeatureFlags.h>

#include <AzCore/Settings/SettingsRegistry.h>
#include <AzCore/std/string/string.h>

namespace Phoenix
{
    namespace
    {
        //! Settings registry root for Phoenix feature flags.
        constexpr const char* FeatureFlagRoot = "/Phoenix/FeatureFlags/";

        bool IsExperimental(FeatureFlag flag)
        {
            switch (flag)
            {
            case FeatureFlag::ExperimentalRendering:
            case FeatureFlag::ExperimentalAI:
            case FeatureFlag::ExperimentalTraversal:
            case FeatureFlag::MultiplayerPrototype:
                return true;
            case FeatureFlag::DebugVisualization:
            case FeatureFlag::PostLaunchFeature:
                return false;
            }
            return false;
        }

        constexpr FeatureFlag AllFlags[] = {
            FeatureFlag::ExperimentalRendering,
            FeatureFlag::ExperimentalAI,
            FeatureFlag::ExperimentalTraversal,
            FeatureFlag::MultiplayerPrototype,
            FeatureFlag::DebugVisualization,
            FeatureFlag::PostLaunchFeature,
        };
    }

    AZStd::string_view ToString(FeatureFlag flag)
    {
        switch (flag)
        {
        case FeatureFlag::ExperimentalRendering:
            return "ExperimentalRendering";
        case FeatureFlag::ExperimentalAI:
            return "ExperimentalAI";
        case FeatureFlag::ExperimentalTraversal:
            return "ExperimentalTraversal";
        case FeatureFlag::MultiplayerPrototype:
            return "MultiplayerPrototype";
        case FeatureFlag::DebugVisualization:
            return "DebugVisualization";
        case FeatureFlag::PostLaunchFeature:
            return "PostLaunchFeature";
        }
        return "Unknown";
    }

    bool IsFeatureEnabled(FeatureFlag flag)
    {
        auto* registry = AZ::SettingsRegistry::Get();
        if (registry == nullptr)
        {
            // No registry means no configuration has been loaded; a feature
            // gate must default to off rather than to whatever was last built.
            return false;
        }

        AZStd::string key = FeatureFlagRoot;
        key += ToString(flag);

        bool enabled = false;
        registry->Get(enabled, key);
        return enabled;
    }

    bool AnyExperimentalFeatureEnabled()
    {
        for (const FeatureFlag flag : AllFlags)
        {
            if (IsExperimental(flag) && IsFeatureEnabled(flag))
            {
                return true;
            }
        }
        return false;
    }
}
