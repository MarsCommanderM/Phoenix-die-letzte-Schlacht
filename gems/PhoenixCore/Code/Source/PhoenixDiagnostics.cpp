#include <Phoenix/Core/PhoenixDiagnostics.h>

#include <AzCore/Debug/Trace.h>

namespace Phoenix
{
    const char* ToString(Severity severity)
    {
        switch (severity)
        {
        case Severity::Trace:
            return "TRACE";
        case Severity::Debug:
            return "DEBUG";
        case Severity::Info:
            return "INFO";
        case Severity::Warning:
            return "WARNING";
        case Severity::Error:
            return "ERROR";
        case Severity::Fatal:
            return "FATAL";
        }
        return "UNKNOWN";
    }

    void EmitDiagnostic(const DiagnosticEvent& event)
    {
        const char* const category = event.category.empty() ? "Phoenix" : event.category.c_str();

        switch (event.severity)
        {
        case Severity::Warning:
            AZ_Warning(category, false, "[%s] %s", ToString(event.severity), event.message.c_str());
            break;
        case Severity::Error:
        case Severity::Fatal:
            AZ_Error(category, false, "[%s] %s", ToString(event.severity), event.message.c_str());
            break;
        default:
            AZ_Printf(category, "[%s] %s\n", ToString(event.severity), event.message.c_str());
            break;
        }
    }
}
