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

    //! Stable short label for a severity, used in emitted diagnostics.
    const char* ToString(Severity severity);

    //! Routes a diagnostic event to the engine trace system, preserving its
    //! severity: Warning and above are raised as warnings/errors rather than
    //! being flattened into plain output.
    void EmitDiagnostic(const DiagnosticEvent& event);
} // namespace Phoenix
