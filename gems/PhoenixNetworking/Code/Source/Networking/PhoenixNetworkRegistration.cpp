#include <Phoenix/Networking/PhoenixNetworkRegistration.h>

#include <AzCore/Debug/Trace.h>

namespace Phoenix
{
    void RegisterPhoenixNetworking()
    {
        AZ_Printf("PhoenixNetworking", "Networking integration ready; AutoComponent generation is supplied by O3DE Multiplayer.\n");
    }
} // namespace Phoenix
