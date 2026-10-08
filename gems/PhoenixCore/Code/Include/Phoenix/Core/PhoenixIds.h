#pragma once

#include <AzCore/Math/Uuid.h>
#include <AzCore/std/functional.h>

namespace Phoenix
{
    //! Strongly typed identity.
    //!
    //! Plain `using MissionId = AZ::Uuid` aliases are mutually assignable, so a
    //! WorldCellId passed where a MissionId is expected compiles silently. The
    //! tag parameter makes each identity a distinct type, which is the point of
    //! typed identities: the mistake becomes a compile error.
    template<typename Tag>
    class PhoenixId
    {
    public:
        PhoenixId() = default;

        explicit PhoenixId(const AZ::Uuid& value)
            : m_value(value)
        {
        }

        static PhoenixId Create()
        {
            return PhoenixId(AZ::Uuid::CreateRandom());
        }

        static PhoenixId Null()
        {
            return PhoenixId(AZ::Uuid::CreateNull());
        }

        const AZ::Uuid& GetValue() const
        {
            return m_value;
        }

        bool IsNull() const
        {
            return m_value.IsNull();
        }

        explicit operator bool() const
        {
            return !IsNull();
        }

        friend bool operator==(const PhoenixId& lhs, const PhoenixId& rhs)
        {
            return lhs.m_value == rhs.m_value;
        }

        friend bool operator!=(const PhoenixId& lhs, const PhoenixId& rhs)
        {
            return !(lhs == rhs);
        }

        friend bool operator<(const PhoenixId& lhs, const PhoenixId& rhs)
        {
            return lhs.m_value < rhs.m_value;
        }

    private:
        AZ::Uuid m_value = AZ::Uuid::CreateNull();
    };

    // Identity tags. Declared, never defined: they exist only to separate types.
    struct CharacterIdTag;
    struct ActionIdTag;
    struct MissionIdTag;
    struct ObjectiveIdTag;
    struct EncounterIdTag;
    struct WorldCellIdTag;
    struct SaveSlotIdTag;
    struct NetworkObjectIdTag;

    using CharacterId = PhoenixId<CharacterIdTag>;
    using ActionId = PhoenixId<ActionIdTag>;
    using MissionId = PhoenixId<MissionIdTag>;
    using ObjectiveId = PhoenixId<ObjectiveIdTag>;
    using EncounterId = PhoenixId<EncounterIdTag>;
    using WorldCellId = PhoenixId<WorldCellIdTag>;
    using SaveSlotId = PhoenixId<SaveSlotIdTag>;
    using NetworkObjectId = PhoenixId<NetworkObjectIdTag>;
}

namespace AZStd
{
    template<typename Tag>
    struct hash<Phoenix::PhoenixId<Tag>>
    {
        size_t operator()(const Phoenix::PhoenixId<Tag>& id) const
        {
            return AZStd::hash<AZ::Uuid>()(id.GetValue());
        }
    };
}
