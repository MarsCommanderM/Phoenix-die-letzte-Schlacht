#pragma once

#include <AzCore/std/string/string_view.h>

namespace Phoenix::Version
{
    //! Product version, the single source of truth for code.
    //!
    //! These values and project/Config/version.json state the same fact in two
    //! places, which is a drift waiting to happen: a release where the launcher
    //! reports 0.2.0 and the binary reports 0.1.0 is a support call nobody can
    //! resolve, because both numbers are "the version". The two are therefore
    //! compared by tools/validation/validate_versions.py, which runs in CI, so
    //! bumping one without the other fails the build rather than shipping.
    //!
    //! Scoped in a Version namespace rather than declared as Phoenix::Major:
    //! a constant called Major at gem scope collides with the next thing that
    //! wants that name, and the collision is a compile error in whichever
    //! translation unit happens to include both.
    inline constexpr unsigned Major = 0;
    inline constexpr unsigned Minor = 1;
    inline constexpr unsigned Patch = 0;

    //! Must equal the "product" field of project/Config/version.json.
    inline constexpr AZStd::string_view Product = "Phoenix";
} // namespace Phoenix::Version
