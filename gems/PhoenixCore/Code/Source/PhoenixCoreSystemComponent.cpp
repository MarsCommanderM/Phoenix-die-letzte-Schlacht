#include <Phoenix/Core/PhoenixCoreSystemComponent.h>

#include <AzCore/Serialization/SerializeContext.h>

namespace Phoenix
{
    void PhoenixCoreSystemComponent::Reflect(AZ::ReflectContext* context)
    {
        if (auto* serializeContext = azrtti_cast<AZ::SerializeContext*>(context))
        {
            serializeContext->Class<PhoenixCoreSystemComponent, AZ::Component>()->Version(1);
        }
    }

    void PhoenixCoreSystemComponent::GetProvidedServices(AZ::ComponentDescriptor::DependencyArrayType& provided)
    {
        provided.push_back(AZ_CRC_CE("PhoenixCoreService"));
    }

    void PhoenixCoreSystemComponent::Activate()
    {
    }

    void PhoenixCoreSystemComponent::Deactivate()
    {
    }
} // namespace Phoenix
