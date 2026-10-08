#pragma once

#include <AzCore/Component/Component.h>
#include <AzCore/Math/Vector3.h>
#include <Phoenix/Character/PhoenixMovementTypes.h>

namespace Phoenix
{
    class PhoenixMovementComponent final
        : public AZ::Component
    {
    public:
        AZ_COMPONENT(PhoenixMovementComponent, "{4D9D0B11-2E42-4A5A-8A37-7B1E4E2D1001}");

        static void Reflect(AZ::ReflectContext* context);

        void SetMoveIntent(const AZ::Vector3& intent);
        MovementState GetMovementState() const
        {
            return m_state;
        }

    protected:
        void Activate() override;
        void Deactivate() override;

    private:
        //! Squared length below which a move intent counts as stationary.
        static constexpr float MoveIntentEpsilonSq = 0.0001f;

        AZ::Vector3 m_moveIntent = AZ::Vector3::CreateZero();
        MovementState m_state = MovementState::Idle;
    };
}
