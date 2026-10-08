#include <AzCore/Debug/Trace.h>
#include <Phoenix/Core/PhoenixDiagnostics.h>

namespace Phoenix
{
    void EmitDiagnostic(const DiagnosticEvent& event)
    {
        AZ_Printf("Phoenix", "[%s] %s\n", event.category.c_str(), event.message.c_str());
    }
}
