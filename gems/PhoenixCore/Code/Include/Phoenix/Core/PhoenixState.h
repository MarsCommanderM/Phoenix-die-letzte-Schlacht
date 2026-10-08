#pragma once

#include <AzCore/std/containers/vector.h>

namespace Phoenix
{
    //! Validated state machine over an enumerated state set.
    //!
    //! Movement, AI and combat are all specified as explicit state machines
    //! (docs/tdd/03-runtime-systems.md). Transitions are validated centrally
    //! rather than by each caller, because an unvalidated transition on the
    //! client produces a state the server will reject — which surfaces as a
    //! desync rather than as the programming error it is.
    template<typename StateEnum>
    class PhoenixStateMachine
    {
    public:
        struct Transition
        {
            StateEnum from;
            StateEnum to;
        };

        PhoenixStateMachine() = default;

        explicit PhoenixStateMachine(StateEnum initial)
            : m_current(initial)
        {
        }

        void AllowTransition(StateEnum from, StateEnum to)
        {
            m_allowed.push_back(Transition{ from, to });
        }

        bool CanTransitionTo(StateEnum to) const
        {
            for (const Transition& transition : m_allowed)
            {
                if (transition.from == m_current && transition.to == to)
                {
                    return true;
                }
            }
            return false;
        }

        //! Returns false and leaves the state unchanged when the transition is
        //! not permitted. Callers are expected to treat that as an error, not
        //! to retry.
        bool TransitionTo(StateEnum to)
        {
            if (!CanTransitionTo(to))
            {
                return false;
            }
            m_previous = m_current;
            m_current = to;
            return true;
        }

        StateEnum GetCurrent() const
        {
            return m_current;
        }

        StateEnum GetPrevious() const
        {
            return m_previous;
        }

    private:
        StateEnum m_current{};
        StateEnum m_previous{};
        AZStd::vector<Transition> m_allowed;
    };
} // namespace Phoenix
