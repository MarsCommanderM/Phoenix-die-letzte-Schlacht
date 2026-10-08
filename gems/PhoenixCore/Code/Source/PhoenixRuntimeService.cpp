#include <Phoenix/Core/PhoenixRuntimeService.h>

#include <AzCore/Debug/Trace.h>
#include <Phoenix/Core/PhoenixBuildInfo.h>

namespace Phoenix
{
    void LogRuntimeStartup()
    {
        const BuildInfo info{};
        AZ_Printf("Phoenix", "Phoenix runtime startup: %s / %s\n", info.buildId, info.engineBaseline);
    }
} // namespace Phoenix
