#pragma once
#include <AzCore/std/string/string.h>

namespace Phoenix
{
    enum class Severity
    {
        Trace,
        Debug,
        Info,
        Warning,
        Error,
        Fatal
    };

    struct DiagnosticEvent
    {
        Severity severity = Severity::Info;
        AZStd::string category;
        AZStd::string message;
    };
}
