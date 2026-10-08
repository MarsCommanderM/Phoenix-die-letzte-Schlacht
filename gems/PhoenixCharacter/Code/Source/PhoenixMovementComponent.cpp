#include <Phoenix/Character/PhoenixMovementComponent.h>
#include <AzCore/Serialization/SerializeContext.h>

namespace Phoenix
{
    void PhoenixMovementComponent::Reflect(AZ::ReflectContext* context)
    {
        if (auto* sc = azrtti_cast<AZ::SerializeContext*>(context))
        {
            sc->Class<PhoenixMovementComponent, AZ::Component>();
        }
    }

    void PhoenixMovementComponent::Activate()
    {
        m_moveIntent = AZ::Vector3::CreateZero();
        m_state = MovementState::Idle;
    }

    void PhoenixMovementComponent::Deactivate()
    {
        m_moveIntent = AZ::Vector3::CreateZero();
    }

    void PhoenixMovementComponent::SetMoveIntent(const AZ::Vector3& intent)
    {
        m_moveIntent = intent;
        if (intent.GetLengthSq() > 0.0001f)
        {
            m_state = MovementState::Walk;
        }
        else
        {
            m_state = MovementState::Idle;
        }
    }
}
