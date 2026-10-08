#include <Phoenix/Core/PhoenixConfig.h>

#include <AzCore/Settings/SettingsRegistry.h>
#include <AzCore/std/string/string.h>

namespace Phoenix::Config
{
    namespace
    {
        AZStd::string FullKey(AZStd::string_view key)
        {
            AZStd::string full = Root;
            full += key;
            return full;
        }
    }

    bool GetBool(AZStd::string_view key, bool fallback)
    {
        auto* registry = AZ::SettingsRegistry::Get();
        if (registry == nullptr)
        {
            return fallback;
        }
        bool value = fallback;
        return registry->Get(value, FullKey(key)) ? value : fallback;
    }

    AZ::s64 GetInt(AZStd::string_view key, AZ::s64 fallback)
    {
        auto* registry = AZ::SettingsRegistry::Get();
        if (registry == nullptr)
        {
            return fallback;
        }
        AZ::s64 value = fallback;
        return registry->Get(value, FullKey(key)) ? value : fallback;
    }

    double GetFloat(AZStd::string_view key, double fallback)
    {
        auto* registry = AZ::SettingsRegistry::Get();
        if (registry == nullptr)
        {
            return fallback;
        }
        double value = fallback;
        return registry->Get(value, FullKey(key)) ? value : fallback;
    }

    bool IsSet(AZStd::string_view key)
    {
        auto* registry = AZ::SettingsRegistry::Get();
        if (registry == nullptr)
        {
            return false;
        }
        return registry->GetType(FullKey(key)) != AZ::SettingsRegistryInterface::Type::NoType;
    }
}
