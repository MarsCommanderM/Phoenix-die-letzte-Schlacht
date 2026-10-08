#include <Phoenix/Character/PhoenixMovementComponent.h>

#include <AzCore/Serialization/SerializeContext.h>

namespace Phoenix
{
    void PhoenixMovementComponent::Reflect(AZ::ReflectContext* context)
    {
        if (auto* serializeContext = azrtti_cast<AZ::SerializeContext*>(context))
        {
            serializeContext->Class<PhoenixMovementComponent, AZ::Component>()->Version(1);
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
        m_state = MovementState::Idle;
    }

    void PhoenixMovementComponent::SetMoveIntent(const AZ::Vector3& intent)
    {
        m_moveIntent = intent;

        // Intent only distinguishes moving from stationary at this stage;
        // gait selection (Sprint/Crouch/...) is owned by gameplay rules that
        // are not implemented in this baseline.
        m_state = intent.GetLengthSq() > MoveIntentEpsilonSq ? MovementState::Walk : MovementState::Idle;
    }
} // namespace Phoenix
