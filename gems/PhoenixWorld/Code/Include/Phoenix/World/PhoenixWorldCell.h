#pragma once

#include <AzCore/Math/Aabb.h>
#include <Phoenix/Core/PhoenixIds.h>

namespace Phoenix
{
    //! Streaming and activation are three distinct levels; conflating them is
    //! the fastest route to the scaling risk in docs/tdd/10-risks.md.
    enum class CellActivation
    {
        Unloaded,     //!< Nothing resident.
        AssetLoaded,  //!< Assets resident, nothing simulating.
        WorldActive,  //!< Entities activated, gameplay logic still off.
        GameplayActive //!< Encounters, AI and gameplay logic running.
    };

    struct WorldCell
    {
        WorldCellId id = WorldCellId::Null();
        AZ::Aabb bounds = AZ::Aabb::CreateNull();
        CellActivation activation = CellActivation::Unloaded;

        //! Resident memory budget for this cell; see docs/tdd/07-budgets.md.
        AZ::u64 memoryBudgetBytes = 0;

        //! Streaming priority; higher loads first within the budget.
        AZ::u32 priority = 0;
    };
}
