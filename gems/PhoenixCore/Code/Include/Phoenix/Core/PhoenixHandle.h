#pragma once

#include <AzCore/base.h>
#include <AzCore/std/limits.h>

namespace Phoenix
{
    //! A generational handle into a dense pool.
    //!
    //! Distinct from PhoenixId: an id names a thing for its whole life and is
    //! stable across sessions and saves, while a handle names a *slot* and is
    //! valid only while that slot holds the generation it was issued for.
    //! The generation is what makes a stale handle detectable instead of
    //! silently addressing whatever now occupies the slot.
    template<typename Tag>
    class PhoenixHandle
    {
    public:
        using IndexType = AZ::u32;
        using GenerationType = AZ::u32;

        static constexpr IndexType InvalidIndex = AZStd::numeric_limits<IndexType>::max();

        PhoenixHandle() = default;

        PhoenixHandle(IndexType index, GenerationType generation)
            : m_index(index)
            , m_generation(generation)
        {
        }

        IndexType GetIndex() const
        {
            return m_index;
        }

        GenerationType GetGeneration() const
        {
            return m_generation;
        }

        bool IsValid() const
        {
            return m_index != InvalidIndex;
        }

        explicit operator bool() const
        {
            return IsValid();
        }

        friend bool operator==(const PhoenixHandle& lhs, const PhoenixHandle& rhs)
        {
            return lhs.m_index == rhs.m_index && lhs.m_generation == rhs.m_generation;
        }

        friend bool operator!=(const PhoenixHandle& lhs, const PhoenixHandle& rhs)
        {
            return !(lhs == rhs);
        }

    private:
        IndexType m_index = InvalidIndex;
        GenerationType m_generation = 0;
    };
}
