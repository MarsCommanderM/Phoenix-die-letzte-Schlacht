#pragma once

#include <AzCore/std/string/string_view.h>

namespace Phoenix
{
    //! Typed access to Phoenix configuration.
    //!
    //! Configuration is read through here rather than from scattered literals,
    //! so that every production parameter has a single source. Values live
    //! under the project-owned settings root; see
    //! docs/implementation/verified-boundaries.md for why the project does not
    //! reuse the engine's own roots.
    namespace Config
    {
        //! Project-owned settings registry root.
        constexpr const char* Root = "/Phoenix/";

        bool GetBool(AZStd::string_view key, bool fallback);
        AZ::s64 GetInt(AZStd::string_view key, AZ::s64 fallback);
        double GetFloat(AZStd::string_view key, double fallback);

        //! True when the key is present, which distinguishes "configured to the
        //! default" from "not configured" — a distinction a fallback hides.
        bool IsSet(AZStd::string_view key);
    } // namespace Config
} // namespace Phoenix
